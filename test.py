import matplotlib.pyplot as plt
import pandas as pd
from pypylon import pylon
import argparse

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
