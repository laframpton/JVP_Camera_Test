import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
