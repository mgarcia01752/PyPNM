from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

class SingleChannelAnalysisOutput(BaseModel):
    """
    PNM analysis output for a single channel (e.g., RxMER or Channel Estimation).

    Contains:
    - amplitude: Amplitude values in specified units
    - frequency: Subcarrier frequencies in Hz
    - time: Optional time points for amplitude measurements in seconds
    - csv_file: Path to the CSV file of the raw data
    - plot_file: Path to the generated PNG graph
    """
    amplitude: List[float] = Field(..., description="Amplitude measurement values")
    amplitude_unit: str = Field(..., description="Unit of amplitude values, e.g., 'dB' or 'dBmV'")
    frequency: Optional[List[float]] = Field(None, description="Subcarrier frequencies in Hz")
    time: Optional[List[float]] = Field(None, description="Time points for amplitude measurements in seconds")
    csv_file: Path = Field(..., description="Filesystem path to the serialized CSV data file")
    plot_file: Path = Field(..., description="Filesystem path to the generated PNG plot")

    def to_csv(self, directory: Path) -> Path:
        """
        Serialize the analysis data to a CSV file in the specified directory.
        """
        directory.mkdir(parents=True, exist_ok=True)
        file_name = f"single_channel_analysis_{self.amplitude_unit}.csv"
        file_path = directory / file_name

        import csv
        with file_path.open("w", newline="") as f:
            writer = csv.writer(f)
            # Determine header and rows based on available data
            if self.time is not None:
                writer.writerow(["time_s", f"amplitude_{self.amplitude_unit}"])
                rows = zip(self.time, self.amplitude)
            elif self.frequency is not None:
                writer.writerow(["frequency_hz", f"amplitude_{self.amplitude_unit}"])
                rows = zip(self.frequency, self.amplitude)
            else:
                writer.writerow([f"amplitude_{self.amplitude_unit}"])
                rows = ([a] for a in self.amplitude)

            for row in rows:
                writer.writerow(row)

        self.csv_file = file_path
        return file_path

    def plot(self, output_file: Optional[Path] = None) -> Path:
        """
        Generate a PNG plot of amplitude vs time or frequency.
        """
        from matplotlib import pyplot as plt

        plt.figure()
        if self.time is not None:
            x, xlabel = self.time, "Time (s)"
        elif self.frequency is not None:
            x, xlabel = self.frequency, "Frequency (Hz)"
        else:
            x, xlabel = list(range(len(self.amplitude))), "Index"

        plt.plot(x, self.amplitude)
        plt.xlabel(xlabel)
        plt.ylabel(f"Amplitude ({self.amplitude_unit})")
        plt.grid(True)

        save_path = output_file or self.plot_file
        plt.savefig(save_path)
        plt.close()
        self.plot_file = save_path
        return save_path
