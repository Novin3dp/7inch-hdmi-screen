"""Make the generic helpers of the HDMI board generator (sexpr, symlib, silk) importable.

Appended to the END of sys.path so this directory's design.py always wins over the HDMI one.
"""
import os
import sys

_HDMI_GEN = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "hardware", "gen"))
if _HDMI_GEN not in sys.path:
    sys.path.append(_HDMI_GEN)
