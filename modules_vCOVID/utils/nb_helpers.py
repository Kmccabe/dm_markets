import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib as mpl
import matplotlib.ticker as tckr
import os
import time
import matplotlib.colors as colors
import moviepy

def format_df_for_boxplot(data_df, x_var, y_var, x_range=None):
    """Reformats dataframe to be a matrix of [[y_1, ..., y_n]], [[y_2, ..., y_n]], ...]; length = length of x; indexes correspond to x's; for use in the box-plotting functions
        x_range (iterable): If using non-numeric x, need to specify a custom range for these, as the function cannot otherwise parse the data range.
    """

    matrix_out = []
    
    # If not provided, figure out x-range
    if x_range is None:
        x_min = data_df[x_var].min()
        x_max = data_df[x_var].max()
        x_range = range(x_min, x_max+1)

    # Traverse the dataframe
    for x in x_range:
        x_match = data_df[data_df[x_var]==x]
        y_vals = list(x_match[y_var].values)
        this_row = y_vals
        matrix_out.append(this_row)
    
    return matrix_out

def avg_df_obs(df_data, x_var, y_var, form="mean", percentiles=None):
    """Return the central tendency of the y_var observations, grouped on the x_var.
        form = mean or median
        percentiles (list) = None or list of percentiles to return
    """

    grouped = df_data[[x_var, y_var]].groupby(x_var)

    # Calc mean
    if form == "mean":
        df_out = grouped.mean()

    # Calc median
    elif form == "median":
        df_out = grouped.median()
        
    # Calc percentiles
    if percentiles is not None:
        for perc in percentiles:
            colname = y_var + "_q_" + str(perc)
            perc_frame = grouped.quantile(q=perc)
            perc_frame = perc_frame.rename(columns={y_var: colname})
            df_out = df_out.join(perc_frame)
    
    return df_out.reset_index()

def compare_graph(dfs, 
                  x_var="week", y_var="eff", 
                  form="line", form_type="mean", 
                  line_labs=None, title=None, 
                  x_ticks=None, x_tick_labs=None, 
                  x_name=None, y_name=None):
    """If not line_labs list provided, uses the names of the simulations in the dataframes. Pass the line lab as the treatments you want, and name the simulations according to these label names as well.

    TODO: Doc this

    """

    if line_labs is None:
        line_labs = []
        for i in range(len(dfs)):
            line_labs.append(dfs[i]["sim_name"].values[0])

    if x_tick_labs is None and x_ticks is not None:
        x_tick_labs = x_ticks

    plt.figure()
    plt.title(title)
    if x_name is None:
        x_name = x_var.capitalize()
    if y_name is None:
        y_name = y_var.capitalize
    plt.xlabel(x_name)
    plt.ylabel(y_name)

    if x_ticks is not None:
        if x_tick_labs is not None:
            plt.xticks(ticks=x_ticks, labels=x_tick_labs)
        else:
            plt.xticks(ticks=x_ticks)
    elif x_tick_labs is not None:
        plt.xticks(labels=x_tick_labs)
    
    if line_labs is not None:
        treat_names = line_labs
    else:
        treat_names = dfs.sim_name.unique()

    for i in range(len(treat_names)):
        this_lab = treat_names[i]
        this_df = dfs[dfs['sim_name']==this_lab]
        mean_df = avg_df_obs(this_df, x_var, y_var, form_type)
        plt.plot(mean_df[x_var], mean_df[y_var], label=this_lab)
    
    plt.legend()
    plt.show()
    
def three_d_grid(grid_size):
    """Transforms a grid size into a projected-vector 3d grid - represented as a nm and mn vectors"""    
    # create dimmensions - currently only for square grid of nXn
    colnames = ['D1', 'D2']
    grid_base = []
    n = np.arange(grid_size)
    m = np.arange(grid_size)
    for n1 in n:
        for m1 in m:
            grid_base.append([n1, m1])

    grid_df = pd.DataFrame(data=grid_base, columns=colnames)
    return grid_df

def plottable_locs(locs, grid_df, investigated="agents"):
    """Plots a location-agents dictionary onto a 3d grid based projects vectors"""
    grid_new = grid_df.copy()
    grid_new[investigated] = 0
    for loc in locs.keys():
        agent_at_key = len(locs[loc])
        d1 = loc[0]
        d2 = loc[1]
        spot_ind = grid_new[(grid_new['D1'] == d1) & (grid_new['D2'] == d2)].index
        grid_new[investigated].iloc[spot_ind] = agent_at_key
    return grid_new

def collate_loc_plots(sim_df, investigated="agents"):
    """Create large stacked DF with agent locations for every trial, week, and period
        sim_df: dataframe of results
        investigated: the value to report in the collated plotted grid df
        
        returns:
            dataframe of stacked form with the grid and observed vars at the points per trial, week, period
    """
    num_trials = sim_df['num_trials'].loc[0]
    num_weeks = sim_df['num_weeks'].loc[0]
    num_periods = sim_df['num_periods'].loc[0]
    num_rounds = sim_df['num_rounds'].loc[0]
    grid_size = sim_df['grid_size'].loc[0]
    num_traders = sim_df['grid_size'].loc[0]

    grd = three_d_grid(grid_size)
    
    control_cols = ['num_trials', 'num_weeks', 'num_periods', 'num_rounds', 'grid_size', 'num_traders', 'num_units', 'lower_bound', 'upper_bound']
    rel_df = sim_df[list(set(sim_df.columns) - set(control_cols))]

    out_df = pd.DataFrame()

    # Traverse the simulation df and save stacked plots
    for trial in range(num_trials):
        trial_df = rel_df[rel_df['trial']==trial]
        init_ind = trial_df[(trial_df['week']==-1) & (trial_df['period']==-1)].index
        init_loc = trial_df['period_locs'].loc[init_ind].values[0]
        init_plot = plottable_locs(init_loc, grd)
        init_plot['trial'] = trial
        init_plot['week'] = -1
        init_plot['period'] = -1
        out_df = pd.concat([out_df, init_plot], ignore_index=True)
        for week in range(num_weeks):
            week_df = trial_df[trial_df['week']==week]
            for period in range(num_periods):
                per_ind = week_df[week_df['period']==period].index
                per_loc = week_df['period_locs'].loc[per_ind].values[0]
                per_plot = plottable_locs(per_loc, grd)
                per_plot['trial'] = trial
                per_plot['week'] = week
                per_plot['period'] = period
                out_df = pd.concat([out_df, per_plot], ignore_index=True)

    return out_df

def graph_plotted(plotted, title_val=None, hue_val="agents", hue_norm_val=(0, 1), size_val="agent", size_norm_val=(0, 1), legend=False, palette="hot_r",
                 integer_bar=True, subtitle=False):
    """Visualize the data on a 2D grid to show the locations and values of the investigated value"""
    
    g = sns.relplot(
        data=plotted,
        x="D1", y="D2", hue=hue_val, size=size_val,
        palette=palette, hue_norm=hue_norm_val, edgecolor=".7",
        height=10, sizes=(35, 400), size_norm=size_norm_val, legend=False
    )

    if not subtitle:
        subtitle = ""
    
    # Tweak the figure to finalize
    g.set(xlabel=subtitle, ylabel="", aspect="equal", xticks=[], yticks=[], xticklabels=[], yticklabels=[], title=title_val)
    g.despine(left=True, bottom=True)
    g.ax.margins(.03)
    plt.grid()

    if legend:
        bar = g.figure.colorbar(mpl.cm.ScalarMappable(norm=hue_norm_val, cmap=palette),
             ax=plt.gca(), label=hue_val, aspect=100, shrink=0.8)
        
        if integer_bar:
            bar.locator = tckr.MaxNLocator(integer=True)
        

    return g

import warnings
#import moviepy.video.io.ImageSequenceClip
from PIL import Image, ImageFile
# import PIL and PIL.ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

default_movie_stem = "loc_movie"
default_graph_folder = "loc_plots"
if not os.path.isdir(default_graph_folder):
    os.mkdir(default_graph_folder)

def to_len_str(number, str_len):
    base_str = str(number)
    new_str = '0'*(str_len-len(base_str)) + base_str
    return new_str

def movie_plotted(collated_plotted, movie_name=None, graph_folder=None, title_val=None, hue_val="Agents", size_val="Agents", scale="relative", hue_max=None, 
                  size_max=None, week_max=None, period_max=None, include_init=True, fps=1, subtitle=True):
    """
    collated_plotted: one trial (or an average of trials) plotted using 
    movie_name: The name to save the movie under (if not provided - uses default for the notebook + timestamp)
    graph_folder: The name of the folder to save the graphs in (if not provided - uses default for the notebook + new folder timestamp)
    title_val: what title to use
    hue_val: what to place the hue on
    size_val: what to place size on
    scale: the way in which normalization will be applied to graph hues and sizes
    hue_max: used for normalization of hue in absolute scale case
    size_max: used for normalization of size in absolute scale case
    """
    timestamp = int(time.time()*1000000) # integer to not have issues with os
    if graph_folder is None:
        graph_folder = default_graph_folder + "/plots_" + str(timestamp)
    else:
        graph_folder = default_graph_folder + "/" + graph_folder
        
    if movie_name is None:
        movie_name = graph_folder + "/movie.mp4"
    else:
        movie_name = graph_folder + "/" + movie_name
        
    if scale == "absolute":
        if hue_max is None:
            raise ValueError("Hue max must be defined for absolute scaling")
        if size_max is None:
            raise ValueError("Size max must be defined for absolute scaling")
    elif scale == "relative":
        hue_max = np.max(collated_plotted[hue_val])
        size_max = np.max(collated_plotted[size_val])
        
    hue_norm = colors.Normalize(vmin=0, vmax=hue_max)
    size_norm = colors.Normalize(vmin=0, vmax=size_max)
    
    # Check if directories exists
    if not os.path.isdir(graph_folder):
        os.mkdir(graph_folder)

    if os.path.isfile(movie_name):
        warnings.warn("Movie name already used")
        return
        # raise ValueError("Movie name already used")

    if week_max is None:
        week_max = np.max(collated_plotted['week'])

    week_digits = len(str(week_max))

    if period_max is None:
        period_max = np.max(collated_plotted['period'])

    period_digits = len(str(week_max))

    img_names = []
    if include_init:
        init_plot = collated_plotted[(collated_plotted['week']==-1) & (collated_plotted['period']==-1)]
        init_name = graph_folder + "/init_plot.png"
        img_names.append(init_name)
        if subtitle:
                subtitle = "Initial Position"
        init_graph = graph_plotted(init_plot, title_val=title_val, hue_val=hue_val, hue_norm_val=hue_norm, size_val=size_val, size_norm_val=size_norm, 
                                   legend=True, subtitle=subtitle)
        plt.savefig(init_name)
        plt.close()
    
    for week in range(0, week_max+1):
        for period in range(0, period_max+1):
            this_plot = collated_plotted[(collated_plotted['week']==week) & (collated_plotted['period']==period)]
            weekstr = to_len_str(week, week_digits)
            prdstr = to_len_str(period, period_digits)
            this_image_name = graph_folder + "/w" + weekstr + "p" + prdstr + "_plot.png"
            img_names.append(this_image_name)
            if subtitle:
                subtitle = "Week: "+weekstr+"; Period: "+prdstr
            
            this_graph = graph_plotted(this_plot, title_val=title_val, hue_val=hue_val, hue_norm_val=hue_norm, size_val=size_val, size_norm_val=size_norm,
                                      legend=True, subtitle=subtitle)
            plt.savefig(this_image_name)
            plt.close()
            

    # Create movie out of plotted graphs
    fps = fps
    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(img_names, fps=fps)
    clip.write_videofile(movie_name)

def plot_boxplot_data(boxplot_data, 
                      title=None, y_lab=None, x_lab=None, 
                      x_ticks=None, x_tick_labs=None, 
                      rbars=None, 
                      savename=None, 
                      fig_text=None,
                      xlim=None, ylim=None, 
                      figsize=None, colors=None, 
                      labels=None, legend=False, 
                      n=1):
    """
    Plot data which has been processed by format data for boxplot.
    
    Args:
        boxplot_data (list): a list of boxplot-formatted data. If passed n=1 (default), assumes this is for a single plot and will wrap in another list.
        
        title (str, optional): custom plot title.

        y_lab (str, optional): custom y axis label.

        x_lab (str, optional): custom x axis label.

        x_ticks (list, optional): custom x tick values (where to place tics on x axis).

        x_tick_labs (list, optional): custom x tick labels.

        rbars (list or tuple; or tuple, optional): tuples define start and end of "recession" (event). If provided - prints recession bars like on FED graphs.

        savename (str, optional): file name to save image to. If provided saves to this file instead of showing the image.

        fig_text (str, optional): Custom text to print on the image.

        xlim (tuple, optional): Min and max of the x for the plot
        
        ylim (tuple, optional): Min and max of y for the plot.
        
        figsize (tuple, optional): Size of the plot
        
        colors (list or str, optional): colors to use for your plots
        
        labels (list or str, optional): Labels to use for your plot
        
        legend (bool, optional, default False): show legend or not.

        n (int, optional, default 1): how many plots are defined by the passed boxplot data. If 1, assumes it needs to wrap the data in a list. Required if you want to plot more than one item - otherwise breaks.
    """
    
    # If n=1, wrap
    if n==1:
        boxplot_data = [boxplot_data]
    
    if figsize is None:
        figsize = (8,8)

    if colors is None:
        cmap = plt.get_cmap("rainbow")
        colors = [cmap(i / (n)) for i in range(n)] # n-1
    elif type(colors) is not list and n==1:
        colors = [colors]
    elif len(boxplot_data) != len(colors):
        raise ValueError(f"List of colors ({len(colors)}) and data ({len(boxplot_data)}) are not of the same length.")
    
    if labels is None:
        base_str = "Series "
        labels = [base_str+str(x) for x in range(n)]
    elif type(labels) is not list and n==1:
        labels = [labels]
    elif len(labels) != len(boxplot_data):
        raise ValueError(f"List of labels ({len(labels)}) and data ({len(boxplot_data)}) are not of the same length.")

    fig, ax1 = plt.subplots(figsize=(figsize[0], figsize[1]))
    fig.canvas.manager.set_window_title('Boxplot')
    fig.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.25)
    
    # With one data series, plot in black+red
    if n == 1:
        bp = ax1.boxplot(boxplot_data[0], notch=True, sym='+', vert=1, whis=1.5)
        if labels is None:
            plt.setp(bp['boxes'], color='black')
        else:
            plt.setp(bp['boxes'], color='black', label=labels)
        plt.setp(bp['whiskers'], color='black')
        plt.setp(bp['fliers'], color='red', marker='+')
    else:
        for i in range(n):
            bp = ax1.boxplot(boxplot_data[i], notch=True, sym='+', orientation='vertical', whis=1.5)
            plt.setp(bp['boxes'], color=colors[i], label=labels[i])
            plt.setp(bp['whiskers'], color=colors[i])
            plt.setp(bp['fliers'], color=colors[i], marker='+')

        
    # Add a horizontal grid to the plot, but make it very light in color
    # so we can use it for reading data values but not be distracting
    ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
                   alpha=0.5)
    
    ax1.set(
        axisbelow=True,  # Hide the grid behind plot objects
        title="Distribution of Weekly Efficiencies Across Trials",
        xlabel="Weeks",
        ylabel='Efficiency',
    )

    if legend == True:
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())

    if title is not None:
        ax1.set(title=title)

    if y_lab is not None:
        ax1.set(ylabel=y_lab)

    if x_lab is not None:
        ax1.set(xlabel=x_lab)

    if x_ticks is not None:
        ax1.set_xticks(x_ticks)

    if x_tick_labs is not None:
        ax1.set_xticklabels(x_tick_labs, fontsize=12)

    # Override standard tick labels with provided x_ticks if x_tick_labs not provided
    if x_ticks is not None and x_tick_labs is None:
        ax1.set_xticklabels(x_ticks, fontsize=12)

    # Plot recession/event bars
    if rbars is not None:
        
        # Try to see if this is list of rbar defs or just one
        # Wrap if just one
        try:
            rbars[0][0]
        except:
            rbars = [rbars]

        for rb in rbars:
            plt.axvspan(rb[0], rb[1], color="grey", alpha=0.3)

    # Set min and max x if defined
    if xlim is not None:
        plt.xlim(xlim[0], xlim[1])

    # Set min and max y if defined
    if ylim is not None:
        plt.ylim(ylim[0], ylim[1]) 

    # Add figure text if defined
    if fig_text is not None:
        plt.figtext(1, 0.2, fig_text)

    # If provided savename, save to file
    if savename is not None:
        plt.savefig(savename)
    # Else print to console
    else:
        plt.show()

    # Clear the painters
    plt.clf()


def avg_df_obs(df_data, x_var, y_var, form="mean", percentiles=None):
    """
    Return the central tendency of the y_var observations, grouped on the x_var.
        form = mean or median
        percentiles (list) = None or list of percentiles to return
    """

    grouped = df_data[[x_var, y_var]].groupby(x_var)

    # TODO implement mean
    if form == "mean":
        df_out = grouped.mean()
    # Todo implement median
    elif form == "median":
        df_out = grouped.median()
        
    # Todo implement percentile
    if percentiles is not None:
        for perc in percentiles:
            colname = y_var + "_q_" + str(perc)
            perc_frame = grouped.quantile(q=perc)
            perc_frame = perc_frame.rename(columns={y_var: colname})
            print(df_out.head())
            print(perc_frame.head())
            df_out = df_out.join(perc_frame)
    
    return df_out.reset_index()