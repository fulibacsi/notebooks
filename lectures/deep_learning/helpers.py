import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns


def plot_results_with_hyperplane(X, y, clf, clf_name=None, ax=None):
    df = pd.DataFrame(data=X, columns=['x', 'y'])
    df['label'] = y
    
    x_min, x_max = df.x.min() - .5, df.x.max() + .5
    y_min, y_max = df.y.min() - .5, df.y.max() + .5

    xx, yy = np.meshgrid(np.arange(x_min, x_max, .02), np.arange(y_min, y_max, .02))
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)
    
    if ax is None:
        fig, ax = plt.subplots()
    
    ax.pcolormesh(xx, yy, Z, cmap=plt.cm.Paired)
    ax.scatter(df.x, df.y, c=df.label, edgecolors='k')
    
    if clf_name is not None:
        ax.set_title(clf_name)
    
    return fig