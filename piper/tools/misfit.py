import numpy as np

def waveform(syn, obs, nt, dt):
	adstf = syn - obs
	return np.sqrt(np.sum(adstf * adstf * dt)), adstf

def traveltime(syn, obs, nt, dt):
	cc = abs(np.convolve(obs, np.flipud(syn)))
	tshift = (np.argmax(cc)-nt+1)*dt

	adstf = np.zeros(nt)
	adstf[1:-1] = (syn[2:] - syn[0:-2])/(2.*dt)
	adstf *= 1./(sum(adstf*adstf)*dt)
	adstf *= tshift

	return tshift, adstf