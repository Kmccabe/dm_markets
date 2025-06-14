import pandas as pd
import scipy
import utils.dm_res_helpers as res2

def conduct_stat_test(measure_a, measure_b, test_method, hypothesis_sidedness="one", measure_list=None):
    if measure_a is None and measure_b is None:
        measure_a = measure_list[0]; measure_b = measure_list[1]
    ci = None
    if test_method == "t":
        t_res = scipy.stats.ttest_ind(measure_a, measure_b, alternative=f"{hypothesis_sidedness}-sided")
        test_val = t_res.statistic
        p_val = t_res.pvalue
        ci = t_res.confidence_interval()
    elif test_method == "mwu":
        mwu_res = scipy.stats.mannwhitneyu(measure_a, measure_b, alternative=f"{hypothesis_sidedness}-sided")
        test_val = mwu_res.statistic
        p_val = mwu_res.pvalue
    elif test_method == "kruskal":
        try:
            k_res = scipy.stats.kruskal(measure_a, measure_b)
            test_val = k_res.statistic
            p_val = k_res.pvalue
        except ValueError:
            test_val = None; p_val = None
    elif test_method == "f":
        f_res = scipy.stats.f_oneway(measure_a, measure_b)
        test_val = f_res.statistic
        p_val = f_res.pvalue
    elif test_method == "ks":
        ks_res = scipy.stats.ks_2samp(measure_a, measure_b, alternative=f"{hypothesis_sidedness}-sided")
        test_val = ks_res.statistic
        p_val = ks_res.pvalue
    elif test_method == "page":
        p_res = scipy.stats.page_trend_test(reversed(measure_list))
        test_val = p_res.statistic
        p_val = p_res.pvalue
    
    # Return test statistic, p-value for 2-sided test, and confidence interval
    return test_val, p_val, ci

def aggregate_obs(df, aggregation_method, metric, observation_frequency, measure_frequency):
    """Aggregate measures up to the observation frequency"""
    if aggregation_method == "mean":
        df_ret = df[['trial', measure_frequency, observation_frequency, metric]].groupby(by=['trial', observation_frequency]).mean().reset_index()
    elif aggregation_method == "median":
        df_ret = df[['trial', measure_frequency, observation_frequency, metric]].groupby(by=['trial', observation_frequency]).median().reset_index()
    if aggregation_method == "end":
        max_trials = max(df[measure_frequency])
        df_ret = df[df[measure_frequency] == max_trials]
    return df_ret

def calc_diff(df_a, df_b, metric, measure_method="mean", test_method="ks", compare_method="across", observation_frequency="week", measure_frequency="week", aggregation_method="mean", weeks="all", tr_periods=None, hypothesis_sidedness="two", metric_max=None, multi_adjust = 'bernoulli'):
    """Calculate differences between two dataframes, comparing the desired metric.
    df_a, df_b  - simulation dataframes to difference; df_a should have a higher (>=) expected measure of the metric. I.e. if testing one-sided hypotheses, pass df_a as the x > u. (simply by convention)
    metric - Metric to compare across simulations, Ex: "eff" (efficiency)
    
    measure_method (str) - choose one of the options in which to handle the calculation of the desired metric for differencing. Across options look at one measure per trial, returning a measure, a std. err., and a p-value; within options look at one measure per frequency (week or period) per trial, returning a dataframe with observation count, measure, std. err. (where applicable), and p-value
        - Measure options: "mean" (mean measure across weeks/periods), "auc" (area under curve - similar to mean), "median" (median of measure across), "end" (single measure is final observation) - how to select the measure of each trial (only used in "across")
    
    test_method (str) - Test options: "ks" (kolmogorov-smirnov test), "mwu" (mann-whitney-u test), "t" (t-test) - the statistical test to perform

    compare_method (str) - Compare options: "across", "within" - if comparison is an "across" (one measure per trial) or a "within" (measures = number of frequency appearances)
    
    observation_frequency - "week" or "period" - at what aggregation (default by mean) observation level to conduct "within" option tests. Must have added true period column to use "period" frequency.
    measure_frequency - the frequency with which the metric is observed in the dataframe. Ignored if equivalent to the "frequency"
    aggregation_method - "mean" or "median" - how to aggregate period-level observation up to "week" level if frequency is "week" and "obsevation_frequency" is at the "period" level.
    weeks = "all" or tuple (start, end) - specify over which weeks to calculate the comparison. If not specified, defaults to "all" weeks.
    tr_periods (tuple) or "all": (start, end) - specify over which true periods (cross-week indexed) to caculate the metric. Must specify if asking for a frequency of "period". "all" means all periods.
    # TODO implement subsets for weeks and tr_periods
    hypothesis_sidedness (str) - "one", "two", or "order" - one sided, two sided, or ordered (Jonkheere Terpstra)
    metric_max (float) - the maximum that the observation can be at any point - used for AUC calculation
    """

    if measure_method == "auc" and metric_max is None:
        raise ValueError("Need to pass a metric max for AUC calculation.")

    if test_method == "page":
        if type(df_a) is not list or df_b is not None:
            raise ValueError("For df_a pass a list of dataframes, with expected largest on the left, down to df_n (ordered expectations). Pass df_b as none.")
        df_s = df_a
    else:
        df_s = [df_a, df_b]

    # Check if can check the sidedness
    if hypothesis_sidedness == "order" and test_method != "page":
        raise ValueError("Need to use the Page Trend (page) test for the order sidedness.")

    try:
        for df in df_s:
            df[metric]
    except KeyError:
        raise ValueError("The metric is not containted within at least one of the passed dataframes.")
    
    if observation_frequency == "period" or measure_frequency == "period":
        if observation_frequency == "period" and not measure_frequency == "period": raise ValueError("Cannot disaggregate measure frequency. Check you indicate measure frequency as period is you want period-to-period measures.")
        try:
            for df in df_s:
                df['tr_period']
        except:
            raise ValueError("At least one of the dataframes does not have the tr_period column, required for period-level analysis.")
    
    # We are careful to preserve the original dataframes
    for df_i in range(len(df_s)):
        df_s[df_i] = df_s[df_i].copy()

    if observation_frequency == "week" and measure_frequency == "period":
        for df_i in range(len(df_s)):
            this_df = df_s[df_i]
            this_df = aggregate_obs(this_df, aggregation_method, metric, observation_frequency, "tr_period")
            df_s[df_i] = this_df
    
    # Check we are not many times observing the same metric (inflating N)
    elif observation_frequency == "week" and measure_frequency == "week":
        for df_i in range(len(df_s)):
            this_df = df_s[df_i]
            this_df = this_df[['trial', 'week', metric]].drop_duplicates() # Dropping multi-observations of each week through lense of each period
            df_s[df_i] = this_df
    
    if hypothesis_sidedness == "one" and test_method in ["kruskal", "f"]:
        raise ValueError("Cannot use one-sided hypothesis test with this test type.")

    if weeks != "all":
        for df_i in range(len(df_s)):
            this_df = df_s[df_i]
            this_df = this_df[(this_df['week'] >= weeks[0]) & (this_df['week'] <= weeks[1])]
            df_s[df_i] = this_df

    if tr_periods != "all":
        for df_i in range(len(df_s)):
            this_df = df_s[df_i]
            this_df = this_df[(this_df['tr_period'] >= tr_periods[0]) & (this_df['tr_period'] <= tr_periods[1])]
            df_s[df_i] = this_df
    
    if weeks == "all" and tr_periods == "all":
        # Drop -1, -1 observations - if want these (e.g. for location metrics) specify a range
        for df_i in range(len(df_s)):
            this_df = df_s[df_i]
            this_df = this_df[this_df['week'] >= 0]
            df_s[df_i] = this_df

    if observation_frequency == "week":
        obs_freq = observation_frequency 
    elif observation_frequency == "period":
        obs_freq = "tr_period"

    # Single measure methods
    if compare_method == "across":
        measure_list = []
        for df_i in range(len(df_s)):
            this_df = df_s[df_i]
            if measure_method == "mean": # Mean of periods
                measure_list.append(this_df[['trial', observation_frequency, metric]].groupby(by=['trial']).mean().reset_index()[metric])
                
            elif measure_method == "median": # Median of periods
                measure_list.append(this_df[['trial', observation_frequency, metric]].groupby(by=['trial']).median().reset_index()[metric])
            
            elif measure_method == "end": # Last period
                final_period = max(this_df[obs_freq])
                measure_list.append(this_df[this_df[obs_freq]==final_period][['trial', metric]].copy()[metric])
            
            elif measure_method == "auc": # Area under curve (= mean deviation from max)
                measure_list.append(res2.calc_area_under_curve(this_df, metric, metric_max=metric_max)[metric])

        test_stat, p_val, ci = conduct_stat_test(measure_a=None, measure_b=None, test_method=test_method, hypothesis_sidedness=hypothesis_sidedness, measure_list=measure_list)

        return test_stat, p_val, ci

    # Many measure methods
    elif compare_method == "within":
        ret_df = None
        for i in range(max(df_s[0][obs_freq])+1):
            measure_list = []
            for df_i in range(len(df_s)):
                this_df = df_s[df_i]
                mes = this_df[this_df[obs_freq]==i][metric]
                measure_list.append(mes)
            
            test_stat, p_val, ci = conduct_stat_test(measure_a=None, measure_b=None, test_method=test_method, hypothesis_sidedness=hypothesis_sidedness, measure_list=measure_list)
            tr_df = pd.DataFrame({obs_freq:[i], 'statistic':[test_stat], 'p_value':[p_val], 'confidence_interval':[ci]})
            
            if ret_df is None:
                ret_df = tr_df
            else:
                ret_df = pd.concat([ret_df, tr_df], ignore_index=True)
            
        # Adjust for multiple comparison
        if multi_adjust == 'bernoulli':
            ret_df['p_adj'] = ret_df['p_value']*len(ret_df)
        
        return ret_df
    
