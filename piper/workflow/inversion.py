from piper.workflow.base import base
from piper.modules import pipeline as p, kernel, optimize

class inversion(base):
	def pipe(self):
		for i in range(int(self.niters)):
			p.add_stage(self.add_iter)
			kernel.pipe()
			optimize.pipe()