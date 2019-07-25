from glob import glob
from piper.workflow.base import base
from piper.tools.shell import mkdir, rm, cp, mv
from piper.modules import pipeline as p, solver, misfit

class synthetic(base):
	def setup(self):
		sources = []
		mkdir('output/traces')
		for src_file in glob('sources/*'):
			src = src_file[8:]
			sources.append(src)
			mkdir('output/traces/' + src)
		
		self.update({'sources': sources})
	
	def pipe(self):
		for src in self.sources:
			p.add_stage(solver.import_source, 'traces/%s/CMTSOLUTION' % src, src)
			solver.pipe()
			p.add_stage(self.copy_traces, src)
	
	def copy_traces(self, src):
		cp('scratch/solver/traces/*.sac', 'output/traces/' + src)