# -*- coding: utf-8 -*-
# Copyright 2007-2023 The HyperSpy developers
#
# This file is part of RosettaSciIO.
#
# RosettaSciIO is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RosettaSciIO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RosettaSciIO. If not, see <https://www.gnu.org/licenses/#GPL>.

from pathlib import Path

import numpy as np
import pytest

hs = pytest.importorskip("hyperspy.api", reason="hyperspy not installed")


TEST_DATA_DIR = Path(__file__).parent / "data" / "mrc"


def test_single_image():
    # Acquired from Velox
    s = hs.load(TEST_DATA_DIR / "HAADFscan.mrc")
    assert s.data.shape == (16, 16)
    assert s.axes_manager.signal_shape == (16, 16)
    assert s.axes_manager.navigation_shape == ()

    for axis in s.axes_manager.signal_axes:
        assert axis.scale == 5.679131317138672
        assert axis.offset == 0
        assert axis.units == "nm"


def test_4DSTEM_image():
    # Acquired from Velox
    s = hs.load(TEST_DATA_DIR / "4DSTEMscan.mrc")
    assert s.data.shape == (256, 256, 256)
    assert s.axes_manager.signal_shape == (256, 256)
    assert s.axes_manager.navigation_shape == (256,)


def test_4DSTEM_image_navigation_shape_16_16():
    # Acquired from Velox
    s = hs.load(
        TEST_DATA_DIR / "4DSTEMscan.mrc",
        navigation_shape=(16, 16),
    )
    assert s.data.shape == (16, 16, 256, 256)
    assert s.axes_manager.signal_shape == (256, 256)
    assert s.axes_manager.navigation_shape == (16, 16)


@pytest.mark.parametrize("distributed", [True, False])
def test_4DSTEM_image_navigation_shape_8_32(distributed):
    s = hs.load(
        TEST_DATA_DIR / "4DSTEMscan.mrc",
        navigation_shape=(8, 32),
        distributed=distributed,
    )
    assert s.data.shape == (32, 8, 256, 256)
    assert s.axes_manager.signal_shape == (256, 256)
    assert s.axes_manager.navigation_shape == (8, 32)


def test_mrc_distributed_equal():
    s = hs.load(
        TEST_DATA_DIR / "4DSTEMscan.mrc",
        navigation_shape=(8, 32),
        distributed=False,
    )
    s2 = hs.load(
        TEST_DATA_DIR / "4DSTEMscan.mrc",
        navigation_shape=(8, 32),
        distributed=True,
    )
    np.testing.assert_array_equal(s.data, s2.data)


@pytest.mark.parametrize("distributed", [True, False])
def test_mrc_chunks_equal(distributed):
    s = hs.load(
        TEST_DATA_DIR / "4DSTEMscan.mrc",
        navigation_shape=(8, 32),
        distributed=distributed,
        chunks=(16, 4, 256, 256),
        lazy=True,
    )
    assert s.data.chunks == (
        (
            16,
            16,
        ),
        (
            4,
            4,
        ),
        (256,),
        (256,),
    )


@pytest.mark.parametrize("navigation_shape", [None, (256,), (8, 32), (8, 16, 2)])
def test_mrc_metadata(navigation_shape):
    s = hs.load(
        TEST_DATA_DIR / "4DSTEMscan.mrc",
        metadata_file=TEST_DATA_DIR / "info.txt",
        navigation_shape=navigation_shape,
    )
    if navigation_shape is None:
        navigation_shape = (8, 32)
    shape = navigation_shape[::-1] + (256, 256)
    assert s.data.shape == shape
    assert s.axes_manager.signal_shape == (256, 256)
    assert s.axes_manager.navigation_shape == navigation_shape
    assert s.metadata.Acquisition_instrument.TEM.detector == "CeleritasXS"
    assert s.metadata.Acquisition_instrument.TEM.magnification == "1000"
    assert s.metadata.Acquisition_instrument.TEM.frames_per_second == "40000"


def test_mrc_metadata_auto():
    s = hs.load(TEST_DATA_DIR / "20241021_00405_movie.mrc", lazy=True)
    navigation_shape = (8, 4)
    shape = navigation_shape[::-1] + (4, 8)
    assert s.data.shape == shape
    assert s.axes_manager.signal_shape == (8, 4)
    assert s.axes_manager.navigation_shape == navigation_shape
    assert s.metadata.Acquisition_instrument.TEM.detector == "DESim"
    assert s.metadata.Acquisition_instrument.TEM.magnification == "1000"
    assert s.metadata.Acquisition_instrument.TEM.frames_per_second == "700"
    assert len(s.metadata.General.virtual_images) == 2
    assert len(s.metadata.General.external_detectors) == 1

    assert s.metadata._HyperSpy.navigator is not None

    shape = (
        s.axes_manager._navigation_shape_in_array
        + s.axes_manager._signal_shape_in_array
    )
    assert s.data.shape == shape


@pytest.mark.parametrize(
    "metadata_file",
    [
        TEST_DATA_DIR / "3DSTEM_scan_info.txt",
        TEST_DATA_DIR / "3DTEM_scan_info.txt",
        TEST_DATA_DIR / "3DTEMDiffracting_scan_info.txt",
    ],
)
def test_mrc_metadata_modes(metadata_file):
    s = hs.load(TEST_DATA_DIR / "20241021_00405_movie.mrc", metadata_file=metadata_file)
    diffracting = "STEM" in metadata_file.name or "Diffracting" in metadata_file.name
    s.axes_manager.navigation_axes[0].units = "sec"
    if diffracting:
        s.axes_manager.signal_axes[0].units = "nm^-1"
        s.axes_manager.signal_axes[1].units = "nm^-1"
    else:
        s.axes_manager.signal_axes[0].units = "nm"
        s.axes_manager.signal_axes[1].units = "nm"
