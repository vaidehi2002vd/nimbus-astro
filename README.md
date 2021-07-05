# nimbus - A Bayesian inference framework to constrain kilonovae models
nimbus is a hierarchical Bayesian framework to infer the intrinsic luminosity parameters
of kilonovae (KNe) associated with gravitational-wave (GW) events, based purely on non-detections.
This framework makes use of GW 3-D distance information and electromagnetic upper limits from
a given survey for multiple events, and self-consistently accounts for finite sky-coverage and prob-
ability of astrophysical origin.

## Installation
nimbus can be installed using the following commands:

    git clone git@github.com:sidmohite/nimbus-astro.git
    
    cd nimbus-astro
    
    python setup.py install
    
Note : For best results, installation should be done into a virtual Python/Anaconda environment.

## Data Inputs
In order to use nimbus to constrain kilonova models we first need to ensure we have the relevant
data files and that they have specfic attributes that will be used by the code:

* A `survey file` containing field, pixel and extinction specific information for the survey.
    * Currently the code expects this file to exist as a Python pickle  - `.pkl` file.
    * The file should contain 3 attributes/columns at minimum -
        * `field_ID` - ID specifying which field.
        * `ebv` - E(B-V) extinction value along the line-of-sight of the field.
        * `A_lambda` - the total extinction in a given passband lambda.

* A `data file` containing all observational data for the event(s) from the survey including upper limits for each 
observed field and passband filter as well as associated observation times.
    * The code expects this file to be in `csv` or `txt` format.
    * The file should contain the following attributes/columns at minimum -
        * `jd` - Time of each observation (format : `isot`).
        * `scimaglim` - Limiting magnitude in the science image (at each CCD/observation point) for each observation.
        * `field` - Field ID (integer) labelling the field for the corresponding observation.
        * `fid` - Filter ID (integer) labelling the passband filter used for the corresponding observation.
        * `status` - Status number (interger) indicating if the observation is good to use for the analysis. Convention :
          `status=1` refers to a "good" observation. 
    
* A `skymap file` containing the 3-D GW skymap localization information.
    * The code expects this to be in `fits.gz` format (identical to that released by LIGO for public alerts).

* A `sample_file` containing prior hyperparameter samples drawn according to a assumed prior distribution.
    * The code expects this file to have a `csv` or `txt` format.

## Running Executables
In order to perform the inference, we need to run the executables given in this package in a specific order:

### Single-field inference
To find the likelihood for the data in a given field given the hyperparameter samples, we can make use of the 
`singlefield_calc` [executable](https://github.com/sidmohite/nimbus-astro/blob/master/nimbus/singlefield_calc).
Since a survey would, in general, contain a large number of observed fields with associated data, it is ideal to 
run this executable with parallelized instances on a computing framework such as a high performance cluster.

    Usage: singlefield_calc [options]

    Options:
      -h, --help            show this help message and exit
      --field=FIELD         Field number to calculate the likelihood for.
      --data_file=DATA_FILE
                            File containing all observational data for the event
                            from the survey.
      --survey_file=SURVEY_FILE
                            File containing field, pixel and extinction specific
                            information for the survey.
      --skymap_file=SKYMAP_FILE
                            Skymap file for the event.
      --sample_file=SAMPLE_FILE
                            File containing the points in parameter space to
                            calculate the log-posterior for.
      --t_start=T_START     The start time of the data for the event. Format must
                            be in isot.
      --t_end=T_END         The end time of the data for the event. Format must be
                            in isot.
      --single_band         Indicator that makes the analysis a single-band
                            calculation.
      --output_str=OUTPUT_STR
                            The common string pattern for the files that save the
                            likelhood values for each field.
                            
