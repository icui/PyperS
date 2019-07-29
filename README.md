# Piper

### Introduction

Piper is yet another package for full waveform inversion studies. It features a flexible workflow manager and integration with (EnTK)[https://radicalentk.readthedocs.io/en/latest/].

The workflow of piper consists of 2 levels: stages and tasks. Stages are executed in their creation order. A stage may contain one or more tasks, which are executed in parallel.

![Pipeline](https://github.com/icui/piper-dev/raw/master/doc/img/pipeline.png)

Currently there are two options to execute the pipeline: build-in pipeline tool for small testing tasks and EnTK for large tasks.

### Prerequisites

* Python 3.7 or later
* (Obspy)[https://github.com/obspy/obspy]
* (CuPy)[https://cupy.chainer.org]
* (Mpi4py)[https://mpi4py.readthedocs.io/en/stable/]
* (Cuda)[https://developer.nvidia.com/cuda-zone]
* (Specfem3D Globe)[https://github.com/geodynamics/specfem3d_globe]

### Running examples

Before running, you need to add piper to PATH and PYTHONPATH

````
export PATH=$PATH:<path-to-piper>/scripts
export PYTHONPATH=$PYTHONPATH:<path-to-piper>
````

##### On TigerGPU

````
cd example
ln -s config.tiger.ini config.ini
pirun
````

##### On Summit

````
cd example
ln -s config.summit.ini config.ini
pirun
````
