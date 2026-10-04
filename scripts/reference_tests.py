"""Run: python reference_tests.py. Gates are declared before experiments."""
import unittest
import numpy as np
from parameters import default_parameters
from pressure import line_load, shape, quadrature_weights
from reference_solver import ReferenceSolver, reaction
from wheel_interface import reference_step, WheelState, HeldBoundary, wheel_to_body, wheel_velocity

class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.p=default_parameters();self.s=ReferenceSolver(self.p)

    def test_zero_input(self):
        z=self.s.zero_state()
        for a in [0.,2.,20.]:
            out=self.s.step(z,[0.,0.],a,.01)
            np.testing.assert_array_equal(out,z)
            np.testing.assert_array_equal(self.s.outputs(out,[0.,0.],a,4000)['force'],[0,0])

    def test_zero_C_limit(self):
        z=np.array([[.002,-.001]])
        expected=z+np.array([.3,-.2])*.07
        for C in [np.zeros(2),np.full(2,1e-15)]:
            np.testing.assert_allclose(reaction(z,np.array([.3,-.2]),C,.07),expected,atol=1e-15)

    def test_no_transport_retains_endpoint_memory(self):
        z=np.full_like(self.s.zero_state(),.001)
        np.testing.assert_array_equal(self.s.step(z,[0.,0.],0.,.2),z)
        out=self.s.step(z,[.1,.2],0.,.001)
        np.testing.assert_allclose(out[0],out[-1])

    def test_partial_residence_inflow(self):
        v=np.array([.2,.1]);a=5.;dt=self.p.L/a*2
        z=self.s.step(self.s.zero_state(),v,a,dt)
        np.testing.assert_allclose(z,self.s.steady_state(v,a),rtol=1e-13,atol=1e-15)
        np.testing.assert_array_equal(z[0],[0,0])

    def test_pressure(self):
        x=np.linspace(0,self.p.L,10001);w=quadrature_weights(x)
        for family in ['uniform','trapezoid','quartic']:
            p,d=line_load(x,self.p.L,4000,family)
            self.assertTrue(np.all(p>=0));self.assertLess(abs(w@p-4000),1e-9)
            self.assertLess(abs(d['raw_integral_relative_error']),1e-6)
        for family in ['uniform','quartic']:
            p,d=line_load(x,self.p.L,4000,family)
            self.assertAlmostEqual(d['centroid_m'],self.p.L/2,12)

    def test_pressure_changes_force_not_imposed_state(self):
        z=self.s.steady_state([.2,.1],4.)
        f=[self.s.outputs(z,[.2,.1],4.,4000,k)['force'] for k in ['uniform','trapezoid','quartic']]
        self.assertGreater(np.linalg.norm(f[0]-f[1]),1.)
        np.testing.assert_array_equal(z,self.s.steady_state([.2,.1],4.))

    def test_signs_steady_combined_bound_and_symmetry(self):
        for v in [[.2,0],[-.2,0],[0,.2],[.3,.4]]:
            v=np.array(v);z=self.s.steady_state(v,4.)
            f=self.s.outputs(z,v,4.,4000)['force']
            self.assertLess(f@v,0)
            self.assertLessEqual(np.linalg.norm(f),self.p.mu_s*4000+1e-8)
            opposite=self.s.outputs(-z,-v,4.,4000)['force']
            np.testing.assert_allclose(f,-opposite)

    def test_transient_isotropic_norm_invariant(self):
        s=ReferenceSolver(default_parameters(sigma0_x=200,sigma0_y=200))
        rng=np.random.default_rng(19);z=s.zero_state()
        for _ in range(200):
            v=rng.uniform(-2,2,2);z=s.step(z,v,3.,.002)
            self.assertLessEqual(np.max(np.linalg.norm(200*z,axis=1)),self.p.mu_s+1e-12)

    def test_memory(self):
        z=self.s.step(self.s.zero_state(),[.1,.2],0.,.02)
        f=self.s.outputs(z,[0,0],0,4000)['force']
        self.assertGreater(np.linalg.norm(f),1.)
        self.assertEqual(np.linalg.norm(self.s.outputs(self.s.zero_state(),[0,0],0,4000)['force']),0.)

    def test_eulerian_damping(self):
        p=default_parameters(sigma1_x=.02,sigma1_y=.03,sigma2=.01)
        s=ReferenceSolver(p,1025);z=s.steady_state([.2,.1],5.)
        out=s.outputs(z,[.2,.1],5.,4000)
        # Eulerian rate is zero at steady state, despite nonzero material rate.
        self.assertLess(np.max(abs(out['partial_t_z'][1:-1])),2e-6)
        q=out['normal_line_load']
        expected=-s.weights@(q[:,None]*(p.sigma0*z+p.sigma2*np.array([.2,.1])))
        np.testing.assert_allclose(out['force'],expected,atol=.002)

    def test_force_load_scaling_moment(self):
        z=self.s.steady_state([0,.2],5.)
        a=self.s.outputs(z,[0,.2],5.,4000,'uniform')
        b=self.s.outputs(z,[0,.2],5.,2000,'uniform')
        np.testing.assert_allclose(a['force'],2*b['force'])
        self.assertAlmostEqual(a['Mz'],2*b['Mz'])
        self.assertGreater(a['Mz'],0.) # trailing negative lateral force -> +yaw moment

    def test_candidate_copy_order_and_wheel_sign(self):
        z=self.s.zero_state();w=WheelState(8/self.p.r);b=HeldBoundary(8,0,4000)
        outputs={c:reference_step(self.s,z,w,c,b,.02) for c in [0.,100.,300.]}
        for c in [300.,100.,0.]:
            out=reference_step(self.s,z,w,c,b,.02)
            np.testing.assert_array_equal(out['next_tire_state'],outputs[c]['next_tire_state'])
        np.testing.assert_array_equal(z,self.s.zero_state())
        self.assertLess(outputs[300.]['next_wheel_state'].omega,w.omega)
        self.assertLess(outputs[300.]['force'][-1,0],0.)

    def test_coordinate_power_identity(self):
        f=np.array([-100,20]);v=np.array([8,.3]);d=.3
        self.assertAlmostEqual(wheel_to_body(f,d)@wheel_to_body(v,d),f@v)
        np.testing.assert_allclose(wheel_velocity(8,.3,0,1,1,d),wheel_to_body(v,-d))
        # Wheel rotation contribution (-r*Fx)*omega + Fx*Vx = Fx*vrx.
        self.assertAlmostEqual((-self.p.r*f[0])*20+f@v,f@np.array([8-self.p.r*20,.3]))

    def test_invalid_inputs(self):
        for args in [(self.s.zero_state(),[0,0],-1,.01),(self.s.zero_state(),[np.nan,0],1,.01),
                     (self.s.zero_state(),[0,0],1,0)]:
            with self.assertRaises(ValueError):self.s.step(*args)
        with self.assertRaises(ValueError):line_load(self.s.x,self.p.L,-10)
        with self.assertRaises(ValueError):shape([.2],'trapezoid',.8,.2)
        with self.assertRaises(ValueError):reference_step(self.s,self.s.zero_state(),WheelState(-1),0,HeldBoundary(8,0,4000),.02)
        with self.assertRaises(ValueError):reference_step(self.s,self.s.zero_state(),WheelState(.001,1000),1000,HeldBoundary(8,0,4000),.02)

if __name__=='__main__': unittest.main(verbosity=2)
