import os
import shutil
import time

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import h5py
import cv2


class Figure:
    def __init__(
        self,
        subplot_1=1,
        subplot_2=2,
        fig_size=720,
        ratio=1,
        dpi=300,
        width_ratios=None,
        height_ratios=None,
        hspace=None,
        wspace=None,
    ):
        """
        Initializes a matplotlib figure with configurable subplots, figure size, DPI, aspect ratios, and spacing.
        Sets up figure and axes aesthetics like colors and grid settings.
        """
        self.fig_size = fig_size
        self.ratio = ratio
        self.dpi = dpi
        self.subplot_1 = subplot_1
        self.subplot_2 = subplot_2
        self.width_ratios = width_ratios
        self.height_ratios = height_ratios
        self.hspace = hspace
        self.wspace = wspace

        fig_width, fig_height = fig_size * ratio / dpi, fig_size / dpi
        fs = np.sqrt(fig_width * fig_height)
        self.fs = fs

        self.fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi)

        self.ts = 2
        self.sw = 0.2
        self.pad = 0.21
        self.minor_ticks = True
        self.grid = False
        self.ax_color = "k"
        self.facecolor = "w"
        self.text_color = "k"

    def get_axes(self, flat=True):
        """
        Generates and returns the axes of the figure based on the subplot configuration. Optionally returns all axes as a flat list.
        """
        plt.rcParams.update({"text.color": self.text_color})
        self.fig.patch.set_facecolor(self.facecolor)

        subplots = (self.subplot_1, self.subplot_2)
        self.subplots = subplots
        self.gs = mpl.gridspec.GridSpec(
            nrows=subplots[0],
            ncols=subplots[1],
            figure=self.fig,
            width_ratios=self.width_ratios or [1] * subplots[1],
            height_ratios=self.height_ratios or [1] * subplots[0],
            hspace=self.hspace,
            wspace=self.wspace,
        )

        self.axes = []
        for i in range(self.subplots[0]):
            row_axes = []
            for j in range(self.subplots[1]):
                ax = self.fig.add_subplot(self.gs[i, j])
                row_axes.append(ax)
                self.customize_axes(ax)

                if self.hspace == 0 and i != self.subplots[0] - 1:
                    ax.set_xticklabels([])

            self.axes.append(row_axes)

        if self.subplot_1 == 1 and self.subplot_2 == 1:
            return self.axes[0][0]

        self.axes_flat = [ax for row in self.axes for ax in row]

        if flat:
            return self.axes_flat
        else:
            return self.axes

    def customize_axes(
        self,
        ax,
    ):
        """
        Applies custom settings to axes, including tick parameters, colors, grid visibility, and minor tick settings.
        """
        ax.tick_params(
            axis="both",
            which="major",
            labelsize=self.ts * self.fs,
            size=self.fs * self.sw * 5,
            width=self.fs * self.sw * 0.9,
            pad=self.pad * self.fs,
            top=True,
            right=True,
            direction="inout",
            color=self.ax_color,
            labelcolor=self.ax_color,
        )

        if self.minor_ticks:
            ax.minorticks_on()

            ax.tick_params(
                axis="both",
                which="minor",
                direction="inout",
                top=True,
                right=True,
                size=self.fs * self.sw * 2.5,
                width=self.fs * self.sw * 0.8,
                color=self.ax_color,
            )

        ax.set_facecolor(self.facecolor)

        for spine in ax.spines.values():
            spine.set_linewidth(self.fs * self.sw)
            spine.set_color(self.ax_color)

        if self.grid:
            ax.grid(
                which="major",
                linewidth=self.fs * self.sw * 0.5,
                color=self.ax_color,
                alpha=0.25,
            )

    def save(self, path, bbox_inches="tight", pad_inches=None):
        """
        Saves the figure to the specified path with options for DPI and padding adjustments.
        """
        self.fig.savefig(
            path, dpi=self.dpi, bbox_inches=bbox_inches, pad_inches=pad_inches
        )

        self.path = path


def make_frames(
    path_output,
    ratio=2,
    fig_size=1400,
    lim=25,  # kpc
    marker_color="k",
    marker_size=None,
    facecolor="w",
    ax_color="k",
    N_max=None,
):
    if isinstance(lim, (float, int)):
        lim_x = [-lim, lim]
        lim_y = [-lim, lim]

    # get folder of the data_path
    savefold = path_output.split("/")[:-1]
    savefold = "/".join(savefold) + "/frames/"

    if not os.path.exists(savefold):
        os.makedirs(savefold)
    else:
        shutil.rmtree(savefold)
        os.makedirs(savefold)

    Fig = Figure(ratio=ratio, fig_size=fig_size)
    Fig.facecolor = facecolor
    Fig.ax_color = ax_color
    axs = Fig.get_axes()
    fs = Fig.fs

    for ax in axs:
        ax.axis("equal")

        ax.set_xlim(lim_x)
        ax.set_ylim(lim_y)

        ax.set_xlabel("kpc")
        ax.set_ylabel("kpc")

    with h5py.File(path_output, "r") as file:
        N = file["Header"].attrs["N"]
        M = file["Header"].attrs["NSnapshots"]

        if N_max is None:
            N_max = M
        else:
            N_max = min(N_max, M)

        if marker_size is None:
            marker_size = 100 / N

        time_start = time.time()
        for ii, i in enumerate(range(N_max)):
            t = file[f"{i:04d}"].attrs["Time"]
            POS = file[f"{i:04d}"]["Positions"]

            scatter_xy = axs[0].scatter(
                POS[:, 0],
                POS[:, 1],
                c=marker_color,
                s=fs * marker_size,
                lw=0.0 * fs,
                alpha=1,
            )
            scatter_xz = axs[1].scatter(
                POS[:, 0],
                POS[:, 2],
                c=marker_color,
                s=fs * marker_size,
                lw=0.0 * fs,
                alpha=1,
            )

            text = axs[0].text(
                0.98,
                0.02,
                f"Time: {1e3 * 0.98*t:.2f} Myr",
                horizontalalignment="right",
                verticalalignment="bottom",
                transform=axs[0].transAxes,
                fontsize=fs * 1.5,
                color=ax_color,
            )

            axs[1].set_yticklabels([])
            axs[1].set_ylabel("")

            fig_name = f"render_{ii:04d}.jpg"
            save_path = savefold + fig_name

            Fig.fig.subplots_adjust(
                top=1, bottom=0, right=1, left=0, hspace=0, wspace=0
            )

            Fig.save(save_path)
            plt.close()
            scatter_xy.remove()
            scatter_xz.remove()
            text.remove()

    print(f"Save images time: {time.time() - time_start:.2f} s")

    return


def create_video_from_frames(
    frame_folder, output_video_path, frame_rate=30, resolution=None
):
    # Get a list of all files in the folder
    files = [
        f
        for f in os.listdir(frame_folder)
        if os.path.isfile(os.path.join(frame_folder, f))
    ]
    # Sort files to ensure the correct order
    files.sort()

    # Read the first image to get the dimensions
    first_frame = cv2.imread(os.path.join(frame_folder, files[0]))
    height, width, layers = first_frame.shape

    if resolution:
        width, height = resolution

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(output_video_path, fourcc, frame_rate, (width, height))

    for file in files:
        frame_path = os.path.join(frame_folder, file)
        frame = cv2.imread(frame_path)

        if resolution:
            frame = cv2.resize(frame, (width, height))

        video.write(frame)

    video.release()
    print(f"Video saved to {output_video_path}")
