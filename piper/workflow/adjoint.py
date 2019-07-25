from piper.workflow.base import base
from piper.modules import kernel

class adjoint(base):
	def pipe(self):
		kernel.pipe()