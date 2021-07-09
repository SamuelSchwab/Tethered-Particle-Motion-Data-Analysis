# Description

The TPM Analysis tool was made for the Macromolecular Biochemistry
research group at Leiden University to analyse tethered particle motion
data. The programme loads pre-processed TPM data from data_good.txt
files. These files contain the root mean square values of beads recorded
during the TPM experiment. Each data_good.txt represents a single TPM
experiment done at a certain protein concentration. The data from one
data_good.txt file is referred to as a dataset. From these datasets, the
programme produces five types of figures: histograms, empirical
distribution function plots, 2-dimensional histograms, violin plots, and
simple scatter plots. The histograms are used to fit a gaussian
distribution. The mean parameter(s) from the fit, also known as the max
RMS value, is important for us as it estimates the RMS value with the
highest likelihood. Population distribution of all datasets are
visualised in a 2-dimensional histogram and a violin plot. The simple
scatter plot shows the averaged max RMS values. The empirical
distribution function plots visualise the single datapoints of each
dataset together with the fit function.

# Installation

## Build

The latest build files are available at:
https://drive.google.com/file/d/1E7bto_Pc7FY1djh5EhhPeRAmqwd_fSEW/view?usp=sharing. Once downloaded, unpack the zip file
and run the TPM.exe.

## Source

The programme is written in Python
3.9.5, although newer also work. Create a virtual environment using the
command prompt. I use virtualenv:
<https://pypi.org/project/virtualenv/>. An example to create and run a
virtual environment in C:/Python/TPM Data Analysis:

    cd /
    cd Python
    cd "TPM Data Analysis"
    virtualenv venv
    call venv/scripts/activate.bat

Next place the source files in this folder and install all required
modules:

    pip install -r requirements.txt

Finally, to run the program:

    python TPM.py

# How to use

Some example data, called Example Data, can be found in the data folder.
To run analysis on this, start the program and in the Data Analysis tab
select the data folder in the \"Data Folder\" option. Enter a minimum
RMS value (50 should be good) and a maximum RMS value (170 should be
good). Click the Start button in the bottom right. The program now
analyses the data. During analyses, it takes the data_good.txt files,
creates Kernel Density Estimators, bins the data, and fits the binned
data. When it is done it will save a file containing the analysed data
in the folder output/Example Data. This file is called
configExport.yaml. To generate plots from this analysed data, go to the
Plot tab in the programme and select the configExport.yaml file we just
generated in the \"Load export config\" option. Click on one of the
buttons at the top to get a preview of a plot. For the histogram
previews the programme will show a histogram from a random dataset. The
options for the plots can be edited on the right hand side. Plots can be
saved by checking the Saved option for the plots that you want to save.
Then, click the bottom right Save button. Plots are saved at the
location of the the configExport.yaml. Note: the checkboxes next to
Histogram, 2D Histogram, Violinplot, Simple plot, and the ECDF only collapse or expand the
options for these plots. These checkboxes serve no other purpose.
