#!/usr/bin/env python
import numpy as np
from astropy.time import Time
import pandas as pd
from scipy.integrate import quad
from nimbus import nimbus
from nimbus import skymap_utils as sky_utils
from multiprocessing import Pool
import sys
from optparse import OptionParser

def get_mlims_from_data(df, field_num, T):
    return np.array([np.median(df[(df.field.values==field_num)&\
                   (df.jd.values==t)&(df.status==1)].scimaglim.values) for t
                   in T])

def get_mlims_err_from_data(df, field_num, T):
    return np.array([np.std(df[(df.field.values==field_num)&\
                   (df.jd.values==t)&(df.status==1)].scimaglim.values) for t
                   in T])

def apply_extinction(df, mlims, T, ext_g, ext_r, ext_i):
    obs_fids = np.array([np.unique(df.fid.values[df.jd.values==t])[0] for t in
                       T])
    mlims_ext = np.zeros_like(mlims)
    for i,fid in enumerate(obs_fids):
        if fid==1:
            mlims_ext[i] = mlims[i]-ext_g
        elif fid==2:
            mlims_ext[i] = mlims[i]-ext_r
        elif fid==3:
            mlims_ext[i] = mlims[i]-ext_i
    return mlims_ext

def lc_model_linear(M0, alpha, t_0, t):
    return M0 + alpha*(t-t_0)

def nullevent_mlim_pdf(mlow,mhigh):
    return 1./(mhigh-mlow)

def calc_norm_factors(p_d_f, maglim_errs, mlow, mhigh):
    #mlow,mhigh calculated for M=-10 by default
    norm_factors = np.array([quad(lambda m: quad(
                           lambda d : kne_inf.calc_expit_argument(
                           kne_inf.dlim(m,-10),mlim_err)(d)*p_d_f(d),
                           dmin, dmax)[0], mlow, mhigh)[0] for mlim_err in
                               maglim_errs])
    return norm_factors

def main():
    parser = OptionParser()
    parser.add_option("--field", type = "int", help = "Field number to calculate\
    the likelihood for.")
    parser.add_option("--data_file", type = "str", help = "File containing all\
    observational data for the event from the survey.")
    parser.add_option("--survey_file", type = "str", help = "File containing\
    field, pixel and extinction specific information for the survey.")
    parser.add_option("--skymap_file", type = "str", help = "Skymap file for the\
    event.")
    parser.add_option("--sample_file", type = "str", help = "File containing the\
    points in parameter space to calculate the log-posterior for.")
    parser.add_option("--t_start", type = "str", help = "The start time of the\
    data for the event. Format must be in isot.")
    parser.add_option("--t_end", type = "str", help = "The end time of the data\
    for the event. Format must be in isot.")
    parser.add_option("--single_band", action = 'store_true',
    dest = "single_band", help = "Indicator that makes the analysis a single-band\
    calculation.")
    parser.add_option("--output_str", type = "str", help = "The common string\
    pattern for the files that save the likelhood values for each field.")
    (options, args) = parser.parse_args()

    field_num = options.field
    sample_file = options.sample_file
    survey_file = options.survey_file
    skymap_file = options.skymap_file
    data_file = options.data_file
    t_start = Time(options.t_start,format='isot')
    t_end = Time(options.t_end,format='isot')
    single_band = options.single_band
    output_str = options.output_str

    df_survey = pd.read_pickle(survey_file)
    if df_survey.ebv.values[df_survey.field_ID==field_num][0] > 2.:
        sys.exit('Field has high extinction. Aborting inference.')

    else:
        ext_g = df_survey.A_g.values[df_survey.field_ID==field_num][0]
        ext_r = df_survey.A_r.values[df_survey.field_ID==field_num][0]
        ext_i = df_survey.A_i.values[df_survey.field_ID==field_num][0]
        print('Survey file read')

    data = pd.read_csv(data_file)
    #data.columns = data.columns.str.replace(' ','')

    data_event = data.loc[(data['jd']>=t_start.jd)&(data['jd']<=t_end.jd),:]

    if single_band:
        filter_ids = np.array([1],dtype='int')
        filter_obs_times = np.array([np.unique(data_event.jd.values[(
    			       data_event.field==field_num)&\
    			       (data_event.status==1)])])
    else:
        filter_ids = np.unique(data_event[data_event.field.values==\
    			  field_num].fid)
        filter_obs_times = np.array([np.unique(data_event.jd.values[(
    			       data_event.field==field_num)&\
    			       (data_event.fid.values==fid)&\
    			       (data_event.status==1)]) for fid in
    			       filter_ids])

    skymap_prob = sky_utils.Skymap_Probability(
    					  skymap_fits_file=skymap_file)
    ipix_field = df_survey.ipix.values[df_survey.field_ID==field_num][0]
    field_prob = skymap_prob.calculate_field_prob(ipix_field)
    p_d_f = skymap_prob.construct_margdist_distribution(ipix_field,
    							       field_prob)
    print('No errors in skymap_utils.py')

    kne_inf = nimbus.Kilonova_Inference(
    				   lc_model_funcs = [lc_model_linear,
    				   lc_model_linear, lc_model_linear],
    				   nullevent_mlim_pdf = nullevent_mlim_pdf)
    print('Using nimbus.py for calculations')

    mlims_array = np.array([get_mlims_from_data(data_event, field_num, T) for T
    		      in filter_obs_times])
    maglimerr_array = np.array([get_mlims_err_from_data(data_event, field_num,
    			  T) for T in filter_obs_times])
    mlims_ext_array = np.array([apply_extinction(data_event, mlims, T, ext_g,
    			  ext_r, ext_i) for mlims,T in zip(mlims_array,
    			  filter_obs_times)])

    m_low_a = 15 # hard-coded for GW190425. Fix to take as option
    m_high_a = 23 # hard-coded for GW190425. Fix to take as option
    m_low_t = 15 # hard-coded for GW190425. Fix to take as option
    m_high_t = 23 # hard-coded for GW190425. Fix to take as option
    t0 = t_start.jd
    P_f = field_prob

    theta = np.loadtxt(sample_file)
    y = np.array([kne_inf.calc_infield_mlim_likelihood(th, filter_ids,
    	    mlims_ext_array, t0, filter_obs_times, p_d_f, P_f, maglimerr_array,
    	    m_low_a, m_high_a, m_low_t, m_high_t) for th in theta])

    with open(output_str+str(field_num)+'.txt','ab') as f:
        np.savetxt(f,y,fmt='%.5f')
    f.close()

if __name__=='__main__':
    main()
