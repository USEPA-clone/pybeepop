"""
pybeepop - BeePop+ interface for Python
"""

import os
import platform
import pandas as pd
from .tools import BeePopModel
from .plots import plot_timeseries
import json


class PyBeePop:
    """Python interface for the BeePop+ honey bee colony simulation model"""

    def __init__(
        self,
        lib_file=None,
        parameter_file=None,
        weather_file=None,
        residue_file=None,
        verbose=False,
    ):
        """Create a PyBeePop object connected to a BeePop+ shared library.

        Args:
            lib_file (str, optional): Path to the BeePop+ shared library (.dll or .so).
            parameters_file (str, optional): Path to a txt file of BeePop+ parameters where each line specifies
                parameter=value. Defaults to None.
            weather_file (str, optional): Path to a .csv or comma separated .txt file containing weather data.
                For formatting info see docs/weather_readme.txt. Defaults to None.
            residue_file (str, optional): Path to a .csv or comma separated .txt file containing pesticide residue data.
                Defaults to None.
            verbose (bool, optional): Print additional debugging statements? Defaults to False.

        Raises:
            FileNotFoundError: If a provided file does not exist at the specified path.
            NotImplementedError: If run on a platform that is not 64-bit Windows or Linux.
        """

        self.parent = os.path.dirname(os.path.abspath(__file__))
        self.platform = platform.system()
        self.verbose = verbose
        if lib_file is None:  # detect OS and architecture and use pre-compiled BeePop+ if possible
            if self.platform == "Windows":
                if platform.architecture()[0] == "32bit":
                    raise NotImplementedError(
                        "Windows x86 (32-bit) is not supported by BeePop+. Please run on an x64 platform."
                    )
                else:
                    lib_file = os.path.join(self.parent, "lib/beepop_win64.dll")
            elif self.platform == "Linux":
                lib_file = os.path.join(self.parent, "lib/beepop_linux.so")
                if self.verbose:
                    print(
                        """
                        Running in Linux mode. Trying manylinux/musllinux version.
                        If you encounter errors, you may need to compile your own version of BeePop+ from source and pass the path to your
                        .so file with the lib_file option. Currently, only 64-bit architecture is supported.
                        See the pybeepop README for instructions.
                        """
                    )
            else:
                raise NotImplementedError("BeePop+ only supports Windows and Linux.")
        if not os.path.isfile(lib_file):
            raise FileNotFoundError(
                """
                BeePop+ shared object library does not exist or is not compatible with your operating system. 
                You may need to compile BeePop+ from source (see https://github.com/USEPA/pybeepop/blob/main/README.md for more info.)
                Currently, only 64-bit architecture is supported.
                """
            )
        self.lib_file = lib_file
        self.beepop = BeePopModel(self.lib_file, verbose=self.verbose)
        self.parameters = None
        if parameter_file is not None:
            self.load_parameter_file(self.parameter_file)
        else:
            self.parameter_file = None
        if weather_file is not None:
            self.load_weather(weather_file)
        else:
            self.weather_file = None
        if residue_file is not None:
            self.load_residue_file(self.residue_file)
        else:
            self.residue_file = None
        # self.new_features = new_features # not being used?
        self.output = None

    def set_parameters(self, parameters):
        """Set BeePop+ parameters based on a dictionary {parameter: value}.

        Args:
            parameters (dict): dictionary of parameteres {parameter: value}.

        Raises:
            TypeError: If parameters is not a dict.
            ValueError: If the parameter is not a valid BeePop+ parameter listed in the docs.
        """
        if (parameters is not None) and (not isinstance(parameters, dict)):
            raise TypeError("parameters must be a named dictionary of BeePop+ parameters")
        self.parameters = self.beepop.set_parameters(parameters)

    def get_parameters(self):
        """Return all parameters that have been set by the user."""
        return self.beepop.get_parameters()

    def load_weather(self, weather_file):
        """Load a weather  file. This should be a csv or comma delimited txt file where each row denotes:
        Date(MM/DD/YY), Max Temp (C), Min Temp (C), Avg Temp (C), Windspeed (m/s), Rainfall (mm),
        Hours of daylight (optional).

        Args:
            weather_file (_type_): Path to the weather file (csv or txt).

        Raises:
            FileNotFoundError: If the provided file does not exist at the specified path.
        """
        if not os.path.isfile(weather_file):
            raise FileNotFoundError("Weather file does not exist at path: {}!".format(weather_file))
        self.weather_file = weather_file
        self.beepop.load_weather(self.weather_file)

    def load_parameter_file(self, parameter_file):
        """Load a .txt file of parameter values to set. Each row of the file is a string with the
        format 'paramter=value'.

        Args:
            parameter_file (_type_): Path to a txt file of BeePop+ parameters.


        Raises:
            FileNotFoundError: If the provided file does not exist at the specified path.
            ValueError: If a listed parameter is not a valid BeePop+ parameter specified in the docs.

        """
        if not os.path.isfile(parameter_file):
            raise FileNotFoundError(
                "Paramter file does not exist at path: {}!".format(parameter_file)
            )
        self.parameter_file = parameter_file
        self.beepop.load_input_file(self.parameter_file)

    def load_residue_file(self, residue_file):
        """Load a .csv or comma delimited .txt file of pesticide residues in pollen/nectar.
            Each row should specify Date(MM/DD/YYYY), Concentration in nectar (g A.I. / g),
            Concentration in pollen (g A.I. / g). Values can be specified in scientific
            notation, e.g. "9.00E-08".

        Args:
            residue_file (_type_): Path to the residue .csv or .txt file.

        Raises:
            FileNotFoundError: If the provided file does not exist at the specified path.
        """
        if not os.path.isfile(residue_file):
            raise FileNotFoundError("Residue file does not exist at path: {}!".format(residue_file))
        self.residue_file = residue_file
        self.beepop.load_contam_file(self.residue_file)

    def run_model(self):
        """_summary_

        Raises:
            RuntimeError: If the weather file has not yet been set.

        Returns:
            DataFrame: A DataFrame of the model results for the BeePop+ run.
        """
        # check to see if parameters have been supplied
        if (self.parameter_file is None) and (self.parameters is None):
            print("No parameters have been set. Running with defualt settings.")
        if self.weather_file is None:
            raise RuntimeError("Weather must be set before running BeePop+!")
        self.output = self.beepop.run_beepop()
        return self.output

    def get_output(self, format="DataFrame"):
        """Get the output from the last BeePop+ run.

        Args:
            format (str, optional): Return results as DataFrame ('DataFrame') or
                JSON string ('json')? Defaults to "DataFrame".

        Raises:
            RuntimeError: If there is no output because run_model has not yet been called.

        Returns:
            DataFrame or json str: A DataFrame or JSON string of the model results for the BeePop+ run.
        """
        if self.output is None:
            raise RuntimeError("There are no results to plot. Please run the model first.")
        if format == "json":
            result = json.dumps(self.output.to_dict(orient="list"))
        else:
            result = self.output
        return result

    def plot_output(
        self,
        columns=[
            "Colony Size",
            "Adult Workers",
            "Capped Worker Brood",
            "Worker Larvae",
            "Worker Eggs",
        ],
    ):
        """Plot the output as a time series.

        Args:
            columns (list, optional): List of column names to plot (as strings). Defaults to ["Colony Size", "Adult Workers", "Capped Worker Brood", "Worker Larvae", "Worker Eggs"].

        Raises:
            RuntimeError: If there is no output because run_model has not yet been called.

        Returns:
            Matplotlib Axes: A Matploitlib Axes object for further customization.
        """
        if self.output is None:
            raise RuntimeError("There are no results to plot. Please run the model first.")
        invalid_cols = [col not in self.output.columns for col in columns]
        if any(invalid_cols):
            raise IndexError(
                "The column name {} is not a valid output column.".format(
                    [i for (i, v) in zip(columns, invalid_cols) if v]
                )
            )
        plot = plot_timeseries(output=self.output, columns=columns)
        return plot

    def get_error_log(self):
        """Return the BeePop+ session error log as a string for debugging."""
        return self.beepop.get_errors()

    def get_info_log(self):
        """Return the BeePop+ session info log as a string for debugging."""
        return self.beepop.get_info()

    def version(self):
        """Return the BeePop+ version as a string."""
        version = self.beepop.get_version()
        return version

    def exit(self):
        """Close the connection to the BeePop+ shared library."""
        self.beepop.close_library()
        del self.beepop
        return
