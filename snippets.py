from matplotlib import figure
import matplotlib.pyplot as plt
# sizes1 = [3, 19]
# explode1 = (0, 0.05)
# labels = ('CRD = 1', 'CRD = 0')

# fig1, ax1 = plt.subplots()
# _, _, autopcts = ax1.pie(sizes1,explode= explode1, labels=labels,labeldistance=None, autopct='%1.2f%%',
#         shadow=False,startangle=40, colors=('tab:red', 'tab:blue'))

# plt.setp(autopcts, **{'weight':'bold', 'fontsize':12})
# ax1.set_title('Frauen', fontdict={'fontsize': 17})

# plt.show()


from scipy import stats
import numpy as np
f,(ax1,ax2)=plt.subplots(1,2,sharex=True)
normal=stats.norm(0,1)
x=np.linspace(-4,4,100)
ax1.plot(x,normal.pdf(x))
ax2.plot(x,normal.cdf(x))
ax1.grid()
ax1.set_title('PDF')
ax2.grid()
ax2.set_title('CDF')
ax1.set_xlabel('x')
ax2.set_xlabel('x')
ax1.set_ylabel('f(x)')
ax2.set_ylabel('F(x)')
plt.show()
import pandas as pd
data=pd.read_csv(r'G:\powell\result6\optimizationresult_campaigndata.csv',sep=';',index_col=0)

f,ax=plt.subplots(nrows=2,ncols=2,sharex=True,sharey=True)
ax[0][0].plot(data.loc[:,'joindecision_threshold'])
ax[0][0].set_title('joindecision_threshold')
ax[0][1].plot(data.loc[:,'launchdecision_threshold'])
ax[0][1].set_title('launchdecision_threshold')
ax[1][0].plot(data.loc[:,'raisebid_factor'])
ax[1][0].set_title('raisebid_factor')
ax[1][1].plot(data.loc[:,'risk_factor'])
ax[1][1].set_title('risk_factor')
plt.setp(ax[-1, :], xlabel='# of func evaluations')
plt.setp(ax[:, 0], ylabel='var value')
plt.show()