from glob import glob
import numpy as np
from obspy.core import read
from obspy.core.trace import Trace
from scipy.signal import resample
from piper.tools import misfit
from piper.kernel.base import base
from piper.tools.shell import cp, mkdir
from piper.modules import pipeline as p, solver

class default(base):
	def setup(self):
		# get sources and stations
		traces = glob('traces/*/*.sac')
		stations = set()
		sources = set()
		for trace in traces:
			tr = trace.split('/')
			stations.add(tr[-1][:-4])
			sources.add(tr[-2])
		
		# create directories for sources
		for src in sources:
			mkdir('scratch/kernel/%s/syn' % src)
			mkdir('scratch/kernel/%s/obs' % src)
			mkdir('scratch/kernel/%s/adj' % src)
		
		# save sources and stations
		self.update({'sources': list(sources), 'stations': list(stations)})
	
	def pipe(self):
		for src in self.sources:
			# run forward
			p.add_stage(solver.import_source, 'traces/%s/CMTSOLUTION' % src)
			solver.pipe(1)

			# filter traces
			for rec in self.stations:
				p.add_task(self.preprocess, src, rec)
			
			# add new stage for computing adjoint source
			p.add_stage()

			# compute adjoint source
			for rec in self.stations:
				p.add_task(self.compute_adjoint_source, src, rec)
			
			# run adjoint
			solver.pipe(2)
			p.add_stage(solver.prepare_kernel, src)
		
		solver.pipe_combine_kernels()
	
	def preprocess(self, src, rec):
		# read and process traces
		syn = read('scratch/solver/traces/%s.sac' % rec)[0]
		obs = read('traces/%s/%s.sac' % (src, rec))[0]

		# resample and filter
		nt = len(syn.data)
		obs = Trace(resample(obs.data, num=nt), syn.stats)
		syn.filter('bandpass', freqmin=1/self.period_max, freqmax=1/self.period_min, zerophase=True)
		obs.filter('bandpass', freqmin=1/self.period_max, freqmax=1/self.period_min, zerophase=True)
		
		# write traces
		syn.write('scratch/kernel/%s/syn/%s.sac' % (src, rec))
		obs.write('scratch/kernel/%s/obs/%s.sac' % (src, rec))
	
	def compute_adjoint_source(self, src, rec):
		# read traces
		syn = read('scratch/kernel/%s/syn/%s.sac' % (src, rec))[0]
		obs = read('scratch/kernel/%s/obs/%s.sac' % (src, rec))[0]

		# get arguments
		nt = syn.stats.npts
		dt = syn.stats.delta
		t0 = syn.stats.sac['b']
		t1 = t0 + (nt - 1) * syn.stats.delta
		t = np.linspace(t0, t1, nt)
		adj_path = 'scratch/kernel/%s/adj/%s.adj' % (src, rec)

		# compute misfit and adjoint source
		_, adstf = getattr(misfit, self.misfit)(syn.data, obs.data, nt, dt)

		# save adjoint source
		np.savetxt(adj_path, np.transpose(np.array([t, adstf])), fmt='%.9g')
		solver.import_adjoint_source(adj_path)
	
	def postprocess(self):
		pass