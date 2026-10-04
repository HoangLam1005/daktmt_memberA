"""Generate scientific figures and a source-conditioned reproduction."""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
from matplotlib.patches import Rectangle
from parameters import default_parameters,value
from pressure import line_load
from reference_solver import ReferenceSolver

ROOT=Path(__file__).resolve().parent
FIG=ROOT/'figures'
def save(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)

def main():
    FIG.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2})
    p=default_parameters();s=ReferenceSolver(p,513);v=[.2,.1];a=4;fz=value('Fz');z=s.steady_state(v,a)
    fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    for family in ['uniform','trapezoid','quartic']:
        out=s.outputs(z,v,a,fz,family)
        axes[0,0].plot(s.x,out['normal_line_load']/1000,label=family)
        axes[1,0].plot(s.x,out['traction_line_load'][:,1]/1000,label=family)
    axes[0,0].set(xlabel='Contact coordinate x (m)',ylabel='Normal line load (kN/m)',title='Equal total load: 4000 N');axes[0,0].legend()
    axes[1,0].set(xlabel='Contact coordinate x (m)',ylabel='Lateral traction (kN/m)',title='Same deformation, different force weighting')
    axes[0,1].plot(s.x,z[:,0]*1000,label='zx');axes[0,1].plot(s.x,z[:,1]*1000,label='zy');axes[0,1].legend()
    axes[0,1].set(xlabel='Contact coordinate x (m)',ylabel='Bristle state (mm)',title='State is independent of imposed load shape')
    ax=axes[1,1];ax.set_axis_off()
    ax.set(xlim=(0,1),ylim=(0,1))
    ax.add_patch(Rectangle((.08,.5),.82,.18,facecolor='#edf3f8',edgecolor='#355773'))
    for u in np.linspace(.08,.9,13):ax.plot([u,u+.035*(u-.08)/.82],[.68,.51],color='#355773',lw=1.5)
    ax.text(.04,.77,'Inflow\nx = 0',fontsize=10)
    ax.text(.79,.77,'Outflow\nx = L',fontsize=10)
    ax.annotate('',xy=(.9,.43),xytext=(.08,.43),arrowprops={'arrowstyle':'->','color':'#355773'})
    ax.text(.21,.33,'Transport a = |r omega|',fontsize=10)
    ax.text(.08,.19,'Lever arm: X = L/2 - x',fontsize=10)
    ax.text(.08,.04,'p [N/m] x friction coefficient -> traction -> force [N]',fontsize=10)
    save(fig,'contact_patch')
    # Contact_patch.png is also exposed at the requested logical output name.
    (ROOT/'contact_patch.png').write_bytes((FIG/'contact_patch.png').read_bytes())
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,file,xkey,ykey,label in [(axes[0],'convergence_space.csv','dx_m','state_rms_m','Spatial spacing (mm)'),(axes[1],'convergence_time.csv','dt_s','state_error_m','Time step (ms)')]:
        with (ROOT/'results'/file).open() as f:rows=list(csv.DictReader(f))
        ticks=[float(r[xkey])*1000 for r in rows]
        ax.loglog(ticks,[float(r[ykey]) for r in rows],'o-')
        ax.set_xticks(ticks,[f'{v:.3g}' for v in ticks]);ax.xaxis.set_minor_locator(NullLocator())
        ax.set(xlabel=label,ylabel='State error (m)')
    save(fig,'convergence')
    data=np.load(ROOT/'results/memory_ablation.npz')
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    ax.plot(data['t'],data['force_history'][:,0],label='Preloaded bristles')
    ax.plot(data['t'],data['force_zero'][:,0],'--',label='Zero initial state')
    ax.set(xlabel='Time since slip release (s)',ylabel='Fx (N)',title='Identical instantaneous inputs, different history');ax.legend();save(fig,'memory_ablation')
    # Reconstruct Deur Fig.4 conditions, output magnitude with explicit sign conversion.
    times=np.linspace(0,.25,2501);repro={};fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    for kmh in [20,60]:
        speed=kmh/3.6;angle=np.deg2rad(value('literature_angle'))
        def boundary(t):
            alpha=angle if t>=.05 else 0.
            return [0.,speed*np.sin(alpha)],speed*np.cos(alpha),fz
        r=s.simulate(times,boundary);repro[f'force_{kmh}']=r['force'];repro[f'Mz_{kmh}']=r['Mz']
        ax.plot(times,-r['force'][:,1],label=f'{kmh} km/h')
    ax.set(xlabel='Time (s)',ylabel='Lateral force magnitude -Fy (N)',title='Deur Fig. 4 inputs reconstructed; no digitized-curve fit')
    ax.legend();save(fig,'literature_deur_fig4_reconstruction')
    np.savez_compressed(ROOT/'results/literature_reconstruction.npz',t=times,**repro)
    with (ROOT/'results/literature_reconstruction.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['t_s','Fy20_N','Fy60_N','Mz20_Nm','Mz60_Nm'])
        w.writerows(zip(times,repro['force_20'][:,1],repro['force_60'][:,1],repro['Mz_20'],repro['Mz_60']))
    data=np.load(ROOT/'pilot_reference.npz')
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    for j in [0,1,2]:ax.plot(data['t'],data['force'][j,:,0],label=str(data['trajectory_id'][j]))
    ax.set(xlabel='Time (s)',ylabel='Fx (N)',title='Pilot trajectories (different prescribed excitations)');ax.legend();save(fig,'pilot_forces')
    # Isolate pressure shape on the very same z(t), rather than comparing different inputs.
    boundary=lambda t:([.15+.1*np.sin(25*t),.12],4.,fz)
    times=np.linspace(0,.2,401);fields=s.simulate(times,boundary)['z'];rows=[]
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for family in ['uniform','trapezoid','quartic']:
        outputs=[s.outputs(zz,boundary(t)[0],4.,fz,family) for t,zz in zip(times,fields)]
        force=np.array([o['force'] for o in outputs]);mz=np.array([o['Mz'] for o in outputs])
        axes[0].plot(times,force[:,1],label=family);axes[1].plot(times,mz,label=family)
        for t,f,m in zip(times,force,mz):rows.append([family,t,*f,m])
    for ax in axes:ax.set_xlabel('Time (s)');ax.legend()
    axes[0].set_ylabel('Fy (N)');axes[1].set_ylabel('Mz (N m)');save(fig,'pressure_ablation')
    with (ROOT/'results/pressure_ablation.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['family','t_s','Fx_N','Fy_N','Mz_Nm']);w.writerows(rows)
    print('6 scientific figures and source-conditioned reconstruction written')
if __name__=='__main__':main()
