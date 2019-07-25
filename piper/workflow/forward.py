from piper.workflow.base import base
from piper.modules import solver

class forward(base):
	def pipe(self):
		solver.pipe()