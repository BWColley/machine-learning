# -*- coding: utf-8 -*-
#!/usr/bin/env python
#title           :ml-example.py
#description     :Machine learning examples
#author          :aarora79
#date            :20151112
#version         :0.1.0
#usage           :python ml-example.py
#notes           : Machine learning example for a dataset downloaded from https://archive.ics.uci.edu/ml/datasets
#                  By default the dataset used by this example is located https://archive.ics.uci.edu/ml/datasets/Wine+Quality
#                  however, any dataset available on this site could be used (top level URL fed as input parameter to this program)
#                  as long as the target variable is located in the last column of the CSV containing the dataset.
#python_version  :2.7.10
#==============================================================================
import shutil
import sys
import os
import time
import copy

#pandas and friends
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.tools.plotting import scatter_matrix
from pandas.tools.plotting import parallel_coordinates
from pandas.tools.plotting import radviz

#web scraping related imports
from bs4 import BeautifulSoup
import urlparse
from urlparse import urljoin
import wget

#misc
import pickle
import argparse

#scikit  learn pacakges
from sklearn import metrics
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import r2_score
from sklearn.metrics import classification_report
from sklearn.cross_validation import KFold


from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB

from sklearn import cross_validation
from sklearn.cross_validation import train_test_split


#globals for this file
ML_VERSION           = '0.1.0'
TEMP_DOWNLOAD_FILE   = 'temp_file'
ANCHOR_TAG           = 'a'
FILE_EXTN_OF_INTREST = '.csv'
OK    = 0
ERROR = -1
DEFAULT_WEBSITE_FOR_DATASET    = ['https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/']
DEFAULT_SEPERATOR_FOR_CSV_FILE = ';'
OUTPUT_CSV_FILE_NAME           = 'ml-output.csv'

##############################################################
# _download_progress_bar(c,t,w)
# This function draws a progress bar. 
# inputs: current value, total width, w: ignore
#         
# returns:
def _download_progress_bar(c,t,w):  
    """Displays the progress bar, to be used with a wget function to show download progress.

    This is a private function of this module

    Args: c: current value, t: total value
    Returns: None

    Raises:
    """  
    dots = (c*100)/t
    bar_str = '\r['
    for i in range(dots):
        bar_str += '='
    bar_str += '=>'
    for i in range(100-dots):    
        bar_str += ' '
    bar_str += ']%s%%' % dots
    print bar_str,
    if c == t:
        print ' '

##############################################################
# _plot_classification_report(cr, ds_name = 'dataset', model_name='model', title='Classification report', cmap=plt.cm.Reds)
# This function plots the classification report as a heat map. 
# inputs: cr: classification report, ds: data source name, model_name: name of the model which generated this report, cmap, color map
#         
# returns: None
def _plot_classification_report(cr, ds_name = 'dataset', model_name='model', title='Classification report', cmap=plt.cm.Reds):
    """Displays the classification report as a color map/heap map, used for comparing classification reports generated by various algorithms.

    This is a private function of this module

    Args: c: classification report, ds: data source name, model_name: name of the model which generated this report, cmap, color map
    Returns: None

    Raises
    """
    lines = cr.split('\n')
    classes = []
    plotMat = []

    for line in lines[2 : (len(lines) - 3)]:
        t = line.split()
        classes.append(t[0])
        v = [float(x) for x in t[1: len(t) - 1]]
        plotMat.append(v)

    fig, ax = plt.subplots(1)
    fig = plt.imshow(plotMat, interpolation='nearest', cmap=cmap)
    
    for c in range(len(plotMat)+1):
        for r in range(len(classes)):
            try:
                txt = plotMat[r][c]
                ax.text(c,r,plotMat[r][c],va='center',ha='center')
            except IndexError:
                pass
            
    plt.title(title)
    plt.colorbar()
    x_tick_marks = np.arange(3)
    y_tick_marks = np.arange(len(classes))
    plt.xticks(x_tick_marks, ['precision', 'recall', 'f1-score'], rotation=45)
    plt.yticks(y_tick_marks, classes)
    plt.tight_layout()
    plt.ylabel('Classes')
    plt.xlabel('Measures')
    fig_name = ds_name + '_' + model_name + '.png'
    plt.savefig(fig_name)
    plt.close()

##############################################################
# _run_ml_algo(ds_name, df, model, model_name, **kwargs)
# This function runs the specified machine learning algorithm on the specified dataset.. 
# inputs: cr: ds_name, df, model, model_name, **kwargs
#         
# returns: model name and a dataframe containing the classification scores
def _run_ml_algo(ds_name, df, model, model_name, **kwargs):

    """ Runs the specified machine learning algorithm and returns the classification scores
    This is a private function of this module

    Also write the model to a python pickle. Also displays the classification report as a color map.

    Args: ds_name: dataset name 
          df: dataset represented as a DataFrame
          model: object of the model to be used for machine learning
          model_name: name of the model
          **kwargs: optional arguments needed be the model
    Returns: model_name: name of the model
             df: dataframe containing a mean of the scores (f1, accurace, precision, recall) from running multiple iterations (KFold)
                 of the ML algorithm (specified as an input to this function)
    Raises
    """
    scores = {'precision':[], 'recall':[], 'accuracy':[], 'f1':[]}
    #split the df into traing and test
    # Define our predictors, last column is quality ...which is what we want to predict so it is excluded from the predictor list

    #Very important to note here that the predictors is an array and the to_be_predicted is a scalar
    #so when we use these to create the X and y later on, the X would of type dataframe but the y is simply a pandas.Series
    #this knowledge comes in useful while creating te X_train, X_test, y_train and y_test
    predictors = df.columns[:-1]
    to_be_predicted = df.columns[-1]

    X = df[predictors]
    y = df[to_be_predicted]  

    for train, test in KFold(df.shape[0], n_folds=12, shuffle=True):

        X_train, X_test = X.loc[train,:], X.loc[test,:]
        y_train, y_test = y[train], y[test]
        estimator = model(**kwargs) 

        # Train the algorithm using all the training data
        estimator.fit(X_train, y_train)

        # Make predictions based on the test data
        expected   = y_test
        predicted  = estimator.predict(X_test)
        #classificationReport = classification_report(expected, predicted)
        #print classificationReport
        #_plot_classification_report(classificationReport, ds_name, model_name)

        #calculate the scores
        #print 'score.......... ' + str(metrics.f1_score(expected, predicted, average="weighted"))
        scores['f1'].append(metrics.f1_score(expected, predicted, average="weighted"))  
        scores['precision'].append(metrics.precision_score(expected, predicted, average="weighted"))
        scores['recall'].append(metrics.recall_score(expected, predicted, average="weighted"))
        scores['accuracy'].append(metrics.accuracy_score(expected, predicted))

    #print and plot the last classification report for the last learning iteration
    classificationReport = classification_report(expected, predicted)
    print '---------------------------------------------------------------'
    print 'classification report for ' + ds_name + ', model=' + model_name
    print '---------------------------------------------------------------'
    print classificationReport
    _plot_classification_report(classificationReport, ds_name, model_name)

    #train the model over the entire dataset before storing it on disk
    estimator = model(**kwargs) 
    estimator.fit(X, y)

    #now write the model to a pickle
    outpath = ds_name + '_' + model_name + ".pickle"
    with open(outpath, 'w') as f:
        pickle.dump(estimator, f)
        print 'stored classification report for ' + ds_name + ', model=' + model_name + ' in ' + outpath

    return model_name, pd.DataFrame(scores).mean()

##############################################################
# ingest(config)
# This function performs the ingestion phase of the data science pipeline. Downloads all CSV files discovered from first level
# parsing of the URL list specified.
# inputs: config: config dictionary
#         
# returns: OK/ERROR
def ingest(config):
    """ Runs the ingestion phase of the data science pipeline.
    Downloads all CSV files discovered from first level parsing of the URL list specified.
    config['urllist'] specifies an array of URLs to be parsed to get the CSV files to be downloaded.

    Args: config: dictionary containing the config structure.

    Returns: OK/ERROR
    Raises
    """
    #create a csv file list in the config structure to be used in later phases of the pipeline
    print 'begining ingestion phase...'
    config['csv_file_list'] = []
    #download data from the web
    for url in config['urllist']:
        try:
            print 'downloading ' + url
            if os.path.exists(TEMP_DOWNLOAD_FILE):
                os.remove(TEMP_DOWNLOAD_FILE)
            temp_file = wget.download(url, TEMP_DOWNLOAD_FILE, bar = _download_progress_bar)
            soup = BeautifulSoup(open(temp_file))

            links = soup.findAll(ANCHOR_TAG)

            for link in links:
                download_link = link.get('href')
                #we are assuming that the files we want to download are available at the first level web page itself
                if FILE_EXTN_OF_INTREST in download_link:
                    csv_file_name = download_link
                    download_link = urljoin(url, download_link)
                    #check if this is a parent directory, if so we want to ignore it
                    if download_link not in url:  
                        print 'downloading..' + download_link
                        #delete file from disk if it already exists
                        if os.path.exists(csv_file_name):
                            os.remove(csv_file_name)
                        wget.download(download_link, csv_file_name, bar = _download_progress_bar)                  
                        config['csv_file_list'].append(csv_file_name)

                    else:
                        print'ignoring parent directory link ' + download_link
            os.remove(temp_file)
        except Exception, e:
            print'Exception: ' + str(e)

    print 'CSV file List :'
    print config['csv_file_list']  

    return OK      

##############################################################
# wrangle(config)
# This function performs the wrangling phase of the data science pipeline. 
# Reads the csv files into pandas dataframe and creates a dataset array.
# 
# inputs: config: config dictionary
#         
# returns: OK/ERROR
def wrangle(config):
    """ Runs the wrangling phase of the data science pipeline.
    reads the csv files into pandas dataframe and creates a dataset array.

    Args: config: dictionary containing the config structure.

    Returns: OK/ERROR
    Raises
    """
    print 'begining wrangling phase...'
    config['datasets'] = []

    for csv_file in config['csv_file_list']:
        #store it in a dataframe
        df = pd.read_csv(csv_file, sep = config['seperator'])
        print 'Some description about the dataset..(shape, columns, statisitcal features, head)'
        print df.shape
        print df.columns
        print df.describe()
        print df.head(1)

        #check if there are any null values in the dataset
        if df.isnull().values.any() == True:
            print ' Null values seen in the dataset, handling is currently TBD..'
            print ' probably put a loop through the columns and see which column has null values and replace nulls by the mean'
            print ' Not implemented for now!!!'
        else:
            print 'No null values seen in the dataset, looks good..'

        #store the dataframe in config for use by next stagesin the pipeline..
        #represent ech dataset by a dictionary with the name as the name of the csv files minus the last 4 characters
        config['datasets'].append({ 'name': csv_file[:-len(FILE_EXTN_OF_INTREST)], 'df': df})
        
    return OK

##############################################################
# analyze(config)
# This function performs the analysis phase of the data science pipeline. 
# Runs various machine learning algorithms on the dataset.
# 
# inputs: config: config dictionary
#         
# returns: OK/ERROR
def analyze(config):
    """ Runs the analysis phase of the data science pipeline.
    Uses various machine learning algorithms on the input dataset and returns classification scores and plots confusion matrix.
    Args: config: dictionary containing the config structure.

    Returns: OK/ERROR
    Raises
    """
    print 'begining analyze phase...'

    result_list = []   
    for dataset in config['datasets']:
        print 'Analysing ' + dataset['name']
             

        #run through the models        
        ml, scores = _run_ml_algo(dataset['name'], dataset['df'], RandomForestClassifier, "RandomForestClassifier", n_estimators=50, oob_score=True)
        #print scores
        #store the result as a dictionary
        result = { 'dataset_name': dataset['name'], 'model_name': ml, 
                   'f1-score': scores['f1'], 'precision': scores['precision'],
                   'recall': scores['recall'], 'accuracy': scores['accuracy']
                 }
        result_list.append(result)

        ml, scores = _run_ml_algo(dataset['name'], dataset['df'], LogisticRegression, "LogisticRegression")
        #store the result as a dictionary
        result = { 'dataset_name': dataset['name'], 'model_name': ml, 
                   'f1-score': scores['f1'], 'precision': scores['precision'],
                   'recall': scores['recall'], 'accuracy': scores['accuracy']
                 }
        result_list.append(result)

        ml, scores = _run_ml_algo(dataset['name'], dataset['df'], GaussianNB, "GaussianNB")
        #store the result as a dictionary
        result = { 'dataset_name': dataset['name'], 'model_name': ml, 
                   'f1-score': scores['f1'], 'precision': scores['precision'],
                   'recall': scores['recall'], 'accuracy': scores['accuracy']
                 }
        result_list.append(result)

    result_df = pd.DataFrame(result_list)
    print result_df
    #store the result df in a csv
    result_df.to_csv(OUTPUT_CSV_FILE_NAME)
    return OK

##############################################################
# visualize(config)
# This function performs the visualization phase of the data science pipeline. 
# 
# 
# inputs: config: config dictionary
#         
# returns: OK/ERROR
def visualize(config):

    # Create various visualizations of the data, this would help to create a feature vector
    for dataset in config['datasets']:
        scatter_matrix(dataset['df'], alpha=0.2, figsize=(20, 20), diagonal='kde')
        fig_name = dataset['name'] + '_scatter_matrix' + '.png'
        plt.savefig(fig_name)
        plt.close()

        plt.figure(figsize=(20,20))
        parallel_coordinates(dataset['df'], 'quality')
        fig_name = dataset['name'] + '_parallel_coordinates' + '.png'
        plt.savefig(fig_name)
        plt.close()

        plt.figure(figsize=(20,20))
        radviz(dataset['df'], 'quality')
        fig_name = dataset['name'] + '_radviz' + '.png'
        plt.savefig(fig_name)
        plt.close()

    return OK

##############################################################
# run_pipeline(config)
# This function runs the data science pipeline
# 
# 
# inputs: config: config dictionary
#         
# returns: OK/ERROR
def run_pipeline(config):
    """ Runs the data science pipeline. Invokes top level functions for various data science pipeline phases.
    ingestion ->wrangling -> analysis ->visualization
    
    Args: config: dictionary containing the config structure.

    Returns: OK/ERROR
    Raises
    """

    #do ingestion ->wrangling -> analysis ->visualization
    status = ingest(config)

    if status == OK:
        status = wrangle(config)
    else:
        print 'error in previous stages, skipping wrangling..'

    if status == OK:
        status = analyze(config)
    else:
        print 'error in previous stages, skipping analysis..'

    if status == OK:
        status = visualize(config)
    else:
        print 'error in previous stages, skipping visualization..'

    pipeline_status = 'successfully' if status == OK else 'with errors'
    print 'completed running datascience pipeline ' + pipeline_status

if __name__ == '__main__':
    #main program starts here..    
    #dictionary to hold configuration
    config = {}
    
    #check usage
    banner = 'Machine Learning Example, v' + ML_VERSION + ', '
    description = banner + 'for a dataset downloaded from https://archive.ics.uci.edu/ml/datasets.\
               By default the dataset used by this example is located https://archive.ics.uci.edu/ml/datasets/Wine+Quality,\
               however, any dataset available on this site could be used (top level URL fed as input parameter to this program)\
               as long as the target variable is located in the last column of the CSV containing the dataset.'
    parser = argparse.ArgumentParser(__file__, description=description)
    parser.add_argument('-u','--urllist',     default=DEFAULT_WEBSITE_FOR_DATASET, nargs='*', help='URL list for the top level pages from where the dataset is to be downloaded. Default URL list is ' + str(DEFAULT_WEBSITE_FOR_DATASET), required=False)
    parser.add_argument('-s','--seperator',   default=DEFAULT_SEPERATOR_FOR_CSV_FILE, help='Seperator for CSV file, default is \';\'', required=False)
    
    try:
        args = vars(parser.parse_args())
        
        config['urllist']     = args['urllist']
        config['seperator']   = args['seperator']
        
        print '-----------' + banner + '-----------'
        print 'configuration in use is as follows:'
        print config

        print 'ready to run the datascience pipeline...'
        run_pipeline(config)

    except Exception, e:
        # not all parms supplied, exit from here. The argparse module would have printed the error message
        print 'Exception: ' + str(e)
        sys.exit()