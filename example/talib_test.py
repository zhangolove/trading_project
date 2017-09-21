import numpy
import talib
import matplotlib.pyplot as plt

close = numpy.random.random(100)
output = talib.SMA(close)
plt.plot(output)
plt.plot(close)
plt.ylabel('price')
plt.show()