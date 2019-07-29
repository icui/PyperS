from glob import glob
import numpy as np
from obspy.core import read
from obspy.core.trace import Trace
from scipy.signal import resample
from piper.tools import misfit
from piper.kernel.base import base
from piper.tools.shell import cp, mkdir
from piper.modules import pipeline as p, solver

class classic(base):
	def setup(self):
		""" save list of sources, stations and kernels
		"""
		# get sources and stations
		traces = glob('events/*/*.sac')
		stations = set()
		sources = set()
		for trace in traces:
			tr = trace.split('/')
			stations.add(tr[-1][:-4])
			sources.add(tr[-2])

		# get kernels
		kernels = []
		if self.alpha: kernels.append('alpha')
		if self.beta: kernels.append('beta')
		if self.rho: kernels.append('rho')
		
		# save sources and stations
		self.update({'sources': list(sources), 'stations': list(stations), 'kernels': kernels})
	
	def pipe(self):
		""" run adjoint for each source then sum kernels
		"""
		for src in self.sources:
			# run forward
			solver.pipe(src, 1)

			# filter traces and compute adjoint sources
			for rec in self.stations:
				p.add_task(self.process, src, rec)
			
			# run adjoint
			solver.pipe(src, 2)
		
		# export kernels
		solver.pipe_export_kernels()
	
	def process(self, src, rec):
		""" filter traces and save to scratch directory
		"""
		# create directory for adjoint sources
		mkdir('scratch/kernel/%s' % src)

		# read and process traces
		syn = read('scratch/solver/%s/%s.sac' % (src, rec))[0]
		obs = read('events/%s/%s.sac' % (src, rec))[0]

		# get trace stats
		nt = syn.stats.npts
		dt = syn.stats.delta

		# resample and filter
		obs = Trace(resample(obs.data, num=nt), syn.stats)
		syn.filter('bandpass', freqmin=1/self.period_max, freqmax=1/self.period_min, zerophase=True)
		obs.filter('bandpass', freqmin=1/self.period_max, freqmax=1/self.period_min, zerophase=True)

		# compute adjoint source time function
		_, adstf = getattr(misfit, self.misfit)(syn.data, obs.data, nt, dt)

		# get time steps
		t0 = syn.stats.sac['b']
		t1 = t0 + (nt - 1) * dt
		t = np.linspace(t0, t1, nt)

		# save adjoint source
		adjsrc = np.transpose(np.array([t, adstf]))
		np.savetxt('scratch/kernel/%s/%s.adj' % (src, rec), adjsrc, fmt='%.9g')