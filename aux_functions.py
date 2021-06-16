import numpy
import time
import pandas as pd

from scipy import stats

def getTimeNow():
    return time.strftime("%Y%m%d_%H%M%S")

def lognorm_estimate(data):
    data = data.replace(0,0.5)
    lnx = data.apply(numpy.log)
    mean=lnx.sum()/lnx.size
    aux=((lnx-mean)**2)
    variance= aux.sum()/aux.size
    return mean,variance

def getUniformParams(sample : pd.Series):
    a=0
    b=0
    if(sample.size>2):
        a=sample.dropna().min()
        b=sample.dropna().max()
    else:
        print("ERROR: Sample size is too small")
    return a,b

def TTest(a : pd.Series,b : pd.Series,alpha=0.05): #95% confidence (two tailed)
    num_t= a.mean()-b.mean()
    s_num=(a.size-1)*a.var()+(b.size-1)*b.var()
    df= a.size+b.size-2
    sp=numpy.sqrt((s_num/df))
    t=num_t/(sp*numpy.sqrt((1/a.size)+(1/b.size)))

    cv = stats.t.ppf(1.0 - alpha, df)
    p = (1 - stats.t.cdf(abs(t),df=df))*2
    print("cv = " + str(cv))
    print("t = " + str(t))
    print("p = " + str(p))
    # interpret via critical value
    # if abs(t) <= cv:
    #     print('Accept null hypothesis. (critical value)')
    # else:
    #     print('Reject the null hypothesis. (critical value)')
    # interpret via p-value
    if p > alpha:
        print('Accept null hypothesis. (p-value)')
    else:
        print('Reject the null hypothesis. (p-value)')

    return t,cv,p

def cvmTest(sample : pd.Series, dist: stats.rv_discrete.cdf):
    n = sample.size
    aux = (2*numpy.arange(1,n+1,1)-1)/(2*n)

    values=numpy.sort(sample.dropna())
    dist_values= dist(values)
    t = (1/(12*n)) + numpy.sum((aux-dist_values)**2)
    return t
