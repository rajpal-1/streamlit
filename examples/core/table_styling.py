"""
Adapted from https://pandas.pydata.org/pandas-docs/stable/user_guide/style.html
"""

import numpy as np
import pandas as pd

import streamlit as st


def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'red' if val < 0 else 'black'
    return 'color: %s' % color


def highlight_max(data, color='yellow'):
    """highlight the maximum in a Series or DataFrame"""
    attr = 'background-color: {}'.format(color)
    if data.ndim == 1:  # Series from .apply(axis=0) or axis=1
        is_max = data == data.max()
        return [attr if v else '' for v in is_max]
    else:  # from .apply(axis=None)
        is_max = data == data.max().max()
        return pd.DataFrame(np.where(is_max, attr, ''),
                            index=data.index, columns=data.columns)


# Create a table to be styled in various ways
np.random.seed(24)
df = pd.DataFrame({'A': np.linspace(1, 5, 5)})
df = pd.concat([df, pd.DataFrame(np.random.randn(5, 4), columns=list('BCDE'))],
               axis=1)
df.iloc[0, 2] = np.nan

# Unstyled
st.table(df)

# Custom formatting
st.table(df.style.format('{:.2%}'))

# Colors
st.table(df.style
         .applymap(color_negative_red)
         .apply(highlight_max, color='darkorange', axis=0))

# Add rows
x = st.table(df.style.set_properties(**{
    'background-color': 'black',
    'color': 'lawngreen',
}))
x.add_rows(pd.DataFrame(np.random.randn(3, 5)).style.set_properties(**{
    'background-color': 'lawngreen',
    'color': 'black',
}))
x.add_rows(pd.DataFrame(np.random.randn(2, 5)).style.format(
    lambda value: '' if value > 0 else '*'))
