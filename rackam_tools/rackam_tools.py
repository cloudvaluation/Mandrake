# -*- coding: utf-8 -*-
"""
Created on Wed Oct 04 12:39:34 2017

@author: guillaume.pealat
"""

# -*- coding: utf-8 -*-
"""
Created on Tue May 12 13:40:03 2015

@author: guillaume.pealat
"""
import matplotlib.pyplot as plt
from rackam_datastore import rackam_datastore as rackam
import pandas as pd

def GrabListOfUnderlying(udl_list, 
                         series_name='nav', 
                         display_graphs = True,
                         identifier = 'Bloomberg',
                         rebase = True):
    store = rackam.rackam_datastore('LIVE')
    
    #list that will hold the results
    result_list = []
    
    #Create dictionary for the search
    search_dict = {}
    search_dict['identifier']=identifier
    
    for udl in udl_list:
        search_dict['value']=udl
        result_list.append(store.getSecurity(search_dict).getData()[series_name])
        
    #Concatenate the results in one Data Frame
    UnderlyingDF = pd.concat(result_list, axis=1 )
    #Drop the #N/A
    UnderlyingDF.dropna(inplace=True)
    UnderlyingDF.columns= udl_list
    
    if rebase:
        UnderlyingDF = 100. * UnderlyingDF / UnderlyingDF.iloc[0]
    
    if display_graphs == True:
        UnderlyingDF.plot(kind='line')
        plt.legend(loc='upper left')
    
    store.closedatastore()
    
    return UnderlyingDF

def max_dd(portfolio_nav):
    returns = portfolio_nav / portfolio_nav.shift(1) -1
    """Assumes returns is a pandas Series"""
    r = returns.add(1).cumprod()
    dd = r.div(r.cummax()).sub(1)
    mdd = dd.min()
    end = dd.argmin()
    start = r.loc[:end].argmax()
    return mdd, start, end
    
def ConstructPorfolio(udl_list, 
                      series_name = 'nav', 
                      weights = None, 
                      display_graph= True, 
                      cash_rate = None,
                      cash_name = 'fixing',
                      identifier = 'Bloomberg'):
    if weights is None:
        #If the weights are not filled, we work on an equally weighted basket
        weights = [1./len(udl_list) for i in range(len(udl_list))]
        
    else:
        if len(udl_list) != len(weights):
            print("Weights list should be the same length as the underlying list")
            return
    
    UnderlyingDF = GrabListOfUnderlying(udl_list = udl_list,
                                        series_name = series_name, 
                                        display_graphs = display_graph,
                                        identifier = identifier,
                                        rebase = True)
    
    
    #Calculate the returns    
    returnsdf = UnderlyingDF / UnderlyingDF.shift(1) -1
    #weight the returns
    local = returnsdf * weights
    #Create the result dataframe
    results = pd.DataFrame(local.sum(axis=1))
    results.columns = ['returns']
    
    results['portfolio'] = 100.
    
    #Calculate the portfolio
    for i in range(1, len(results)):
        results.portfolio.iloc[i] = results.portfolio.iloc[i-1] * (1. + results.returns.iloc[i])
    
    if cash_rate is not None:
        results['portfolioER'] = 100.
        
        cashrate = GrabListOfUnderlying(udl_list = [cash_rate],
                                        series_name = cash_name, 
                                        display_graphs = display_graph,
                                        identifier = identifier,
                                        rebase = False)

        results['rate'] = cashrate[cash_rate]
        
        #Calculate the portfolio
        for i in range(1, len(results)):
            dt = (results.index[i] - results.index[i-1]).days
            results.portfolioER.iloc[i] = results.portfolioER.iloc[i-1] * (results.portfolio.iloc[i] / results.portfolio.iloc[i-1] - results.rate.iloc[i-1] * dt / 360 )
    
        del results['rate']
    
    del results['returns']
    
    if display_graph == True:
        results.plot(kind='line')
        plt.legend(loc='upper left')
        
    return results

def PortfolioAnalysis(portfolio):
    def max_dd(returns):
        """Assumes returns is a pandas Series"""
        r = returns.add(1).cumprod()
        dd = r.div(r.cummax()).sub(1)
        mdd = dd.min()
        end = dd.argmin()
        start = r.loc[:end].argmax()
        return mdd, start, end
    
    