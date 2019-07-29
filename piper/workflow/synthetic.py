from glob import glob
from piper.workflow.base import base
from piper.tools.shell import mkdir, mv
from piper.modules import pipeline as p, solver

class synthetic(base):
	def setup(self):
		sources = []
		mkdir('output/traces')
		for src_dir in glob('events/*'):
			src = src_dir[7:]
			sources.append(src)
			mkdir('output/traces/' + src)
		
		self.update({'sources': sources})
	
	def pipe(self):
		for src in self.sources:
			solver.pipe(src, 0)
			p.add_stage(self.copy_traces, src)
	
	def copy_traces(self, src):
		mv('scratch/solver/%s/*.sac' % src, 'output/traces/' + src)