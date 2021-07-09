import numpy as np

def unimodal(x, a, b, c):
	return a*np.exp((-0.5)*np.square(x-b)/np.square(c))

def bimodal(x, a1, b1, c1, a2, b2, c2):
	return a1*np.exp((-0.5)*np.square(x-b1)/np.square(c1)) + a2*np.exp((-0.5)*np.square(x-b2)/np.square(c2))