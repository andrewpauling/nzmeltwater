#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  5 13:10:27 2018

@author: andrewpauling
"""

from __future__ import print_function
import numpy as np
import xarray as xr
import matplotlib.path as mpath
from xgcm import Grid
import requests
from scipy.stats import ttest_ind


def globalmean(da):
    if "lat" in da.dims:
        latvar = "lat"
        lonvar = "lon"
    elif "latitude" in da.dims:
        latvar = "latitude"
        lonvar = "longitude"

    return da.weighted(np.cos(np.deg2rad(da[latvar]))).mean((latvar, lonvar))


def annualmean(da):
    return da.groupby("time.year").mean("time")


def compute_pre(p):
    north = globalmean(p.sel(lat=slice(0, 10)))
    south = globalmean(p.sel(lat=slice(-10, 0)))

    return north - south


def regrid_xgcm(ds, dp_sigma, ps, p_target):
    """
    Regrid data from hybrid-sigma coordinates to constant pressure levels using xgcm
    Uses xgcm.Grid.transform

    Parameters
    ----------
    ds: xarray Dataset
        A dataset containing the variables to be regridded
    dp_sigma: xarray DataArray
        DataArray containing thickness of hybrid-sigma levels in hPa
    ps: xarray DataArray
        DataArray containing surface pressure data
    p_target: array-like
        Array containing pressure levels in hPa to interpolate to

    Returns
    -------
    dsout: xarray Dataset
        A dataset containing the variables regridded onto pressure levels

    """

    p = (ds["hyam"] * ds["P0"] + ds["hybm"] * ps) / 100
    ds = ds.assign({"p": np.log(p)})
    grid = Grid(ds, coords={"Z": {"center": "lev"}}, periodic=False)

    dsout = xr.Dataset(
        coords={
            "time": ("time", ds.time.data),
            "plev": ("plev", p_target),
            "lat": ("lat", ds.lat.data),
            "lon": ("lon", ds.lon.data),
        }
    )

    for var in ds.data_vars:
        if var in ["Q", "T"] or var[0] == "F":
            if var[0] == "F":
                data = ds[var] / dp_sigma
            else:
                data = ds[var]
            varout = grid.transform(data, "Z", np.log(p_target), target_data=ds.p)
            varout = varout.rename({"p": "plev"})
            varout = varout.assign_coords({"plev": p_target})
        else:
            varout = ds[var]

        dsout = dsout.assign({var: varout})
    return dsout


def fixmonth(ds):
    """Fix CESM months since by default the timestamp is for the first day of
    the next month

    Parameters
    ----------

    ds : xarray dataset
            Dataset containing time to fix

    Returns
    -------

    ds : xarray dataset
            Fixed dataset
    """

    mytime = ds["time"][:].data
    for time in range(mytime.size):
        if mytime[time].month > 1:
            mytime[time] = mytime[time].replace(month=mytime[time].month - 1)
        elif mytime[time].month == 1:
            mytime[time] = mytime[time].replace(month=12)
            mytime[time] = mytime[time].replace(year=mytime[time].year - 1)

    ds = ds.assign_coords(time=mytime)

    return ds


def circle(axs):
    theta = np.linspace(0, 2 * np.pi, 100)
    center, radius = [0.5, 0.5], 0.5
    verts = np.vstack([np.sin(theta), np.cos(theta)]).T
    circle = mpath.Path(verts * radius + center)
    axs.set_boundary(circle, transform=axs.transAxes)


def get_corresponding_varname(name):
    namedict = {
        "air_temperature": "tas",
        "toa_incoming_shortwave_flux": "rsdt",
        "toa_outgoing_shortwave_flux": "rsut",
        "toa_outgoing_longwave_flux": "rlut",
        "precipitation_flux": "pr",
        "aice": "siconc",
        "hi": "sivol",
    }

    if name in namedict.keys():
        return namedict[name]
    elif name in namedict.values():
        for k, v in namedict.items():
            if v == name:
                return k
    else:
        raise ValueError("Not a valid UM variable name")


def esgf_search(
    server="https://esgf-node.llnl.gov/esg-search/search",
    files_type="OPENDAP",
    local_node=True,
    project="CMIP6",
    verbose=False,
    format="application%2Fsolr%2Bjson",
    use_csrf=False,
    **search
):
    client = requests.session()
    payload = search
    payload["project"] = project
    payload["type"] = "File"
    if local_node:
        payload["distrib"] = "false"
    if use_csrf:
        client.get(server)
        if "csrftoken" in client.cookies:
            # Django 1.6 and up
            csrftoken = client.cookies["csrftoken"]
        else:
            # older versions
            csrftoken = client.cookies["csrf"]
        payload["csrfmiddlewaretoken"] = csrftoken

    payload["format"] = format

    offset = 0
    numFound = 10000
    all_files = []
    files_type = files_type.upper()
    while offset < numFound:
        payload["offset"] = offset
        url_keys = []
        for k in payload:
            url_keys += ["{}={}".format(k, payload[k])]

        url = "{}/?{}".format(server, "&".join(url_keys))
        print(url)
        r = client.get(url)
        r.raise_for_status()
        resp = r.json()["response"]
        numFound = int(resp["numFound"])
        resp = resp["docs"]
        offset += len(resp)
        for d in resp:
            if verbose:
                for k in d:
                    print("{}: {}".format(k, d[k]))
            url = d["url"]
            for f in d["url"]:
                sp = f.split("|")
                if sp[-1] == files_type:
                    all_files.append(sp[0].split(".html")[0])
    return sorted(all_files)


def regrid_xgcm(ds, vars_to_regrid, p, p_target):
    """
    Regrid data from hybrid-sigma coordinates to constant pressure levels using xgcm
    Uses xgcm.Grid.transform

    Parameters
    ----------
    ds: xarray Dataset
        A dataset containing the variables to be regridded
    vars_to_regrid: list
        List of the names of the variables to be regridded
    p: xarray DataArray
        DataArray containing pressure data
    p_target: array-like
        Array containing pressure levels in hPa to interpolate to

    Returns
    -------
    dsout: xarray Dataset
        A dataset containing the variables regridded onto pressure levels

    """

    ds = ds.assign({"p": np.log(p)})
    grid = Grid(ds, coords={"Z": {"center": "model_level_number"}}, periodic=False)

    dsout = xr.Dataset(
        coords={
            "time": ("time", ds.time.data),
            "plev": ("plev", p_target),
            "lat": ("lat", ds.lat.data),
            "lon": ("lon", ds.lon.data),
        }
    )

    for var in ds.data_vars:
        if var in vars_to_regrid:
            data = ds[var]
            varout = grid.transform(data, "Z", np.log(p_target), target_data=ds.p)
            varout = varout.rename({"p": "plev"})
            varout = varout.assign_coords({"plev": p_target})
        else:
            varout = ds[var]

        dsout = dsout.assign({var: varout})
    return dsout


def stattest(ctrl, expt):
    tstat, pval = ttest_ind(ctrl, expt)

    xpval = xr.DataArray(pval, coords=[ctrl.lat, ctrl.lon], dims=("lat", "lon"))

    tanom = (expt - ctrl).mean("year")

    return xpval, tanom


def cleanocn(ds):
    if "yt" in ds.dims:
        ds = ds.rename({"yt": "lat", "xt": "lon"})
    if "yT" in ds.dims:
        ds = ds.rename({"yT": "j", "xT": "i"})
    if "y" in ds.dims:
        ds = ds.rename({"y": "j"})
    if "x" in ds.dims:
        ds = ds.rename({"x": "i"})
    if "yh" in ds.dims:
        ds = ds.rename({"yh": "j"})
    if "xh" in ds.dims:
        ds = ds.rename({"xh": "i"})
    if "nlat" in ds.dims:
        ds = ds.rename({"nlat": "j"})
    if "nlon" in ds.dims:
        ds = ds.rename({"nlon": "i"})
    if "lat" in ds.dims:
        ds = ds.swap_dims({"lat": "j"})
    if "lon" in ds.dims:
        ds = ds.swap_dims({"lon": "i"})
    if "TLONG" in ds.coords:
        ds = ds.rename({"TLAT": "lat", "TLONG": "lon"})
        
    if "z_l" in ds.dims:
        ds = ds.rename({"z_l": "lev"})
    if "z_t" in ds.dims:
        ds = ds.rename({"z_t": "lev"})
        
    if "deptht" in ds.dims:
        ds = ds.rename({"deptht": "lev"})
    if "depthu" in ds.dims:
        ds = ds.rename({"depthu": "lev"})
    if "depthv" in ds.dims:
        ds = ds.rename({"depthv": "lev"})
    if "depth" in ds.dims:
        ds = ds.rename({"depth": "lev"})
    if "zoc" in ds.dims:
        ds = ds.rename({"zoc": "lev"})
        
    if "nj" in ds.dims and "TLON" in ds.coords:
        ds = ds.rename({"nj": "j", "ni": "i", "TLAT": "lat", "TLON": "lon"})
    elif "nj" in ds.dims and "TLONG" in ds.coords:
        ds = ds.rename({"nj": "j", "ni": "i", "TLAT": "lat", "TLONG": "lon"})

    if "nj" in ds.dims:
        ds = ds.swap_dims({"nj": "j", "ni": "i"})

    if "latitude" in ds.coords:
        ds = ds.rename({"latitude": "lat", "longitude": "lon"})
    elif "nav_lat" in ds.coords:
        ds = ds.rename({"nav_lat": "lat", "nav_lon": "lon"})
    elif "plat" in ds.coords:
        ds = ds.rename({"plat": "lat", "plon": "lon"})
    elif "lono" in ds.coords:
        ds = ds.rename({"lato": "lat", "lono": "lon"}).swap_dims({"lat": "j", "lon": "i"})
    elif "lono2" in ds.coords:
        ds = ds.rename({"lato": "lat", "lono2": "lon"}).swap_dims({"lat": "j", "lon": "i"})
        
    if "time_counter" in ds.dims and ("time_centered" in ds.data_vars or "time_centered" in ds.coords):
        ds = ds.rename({"time_centered": "time"})
        ds = ds.swap_dims({"time_counter": "time"})
        ds = ds.drop("time_counter")
    elif "time_counter" in ds.dims:
        ds = ds.swap_dims({"time_counter": "time"})
        ds = ds.drop("time_counter")

    if "ULON" in ds.data_vars:
        ds = ds.drop_vars(("ULAT", "ULON"))
    elif "ULONG" in ds.data_vars:
        ds = ds.drop_vars(("ULAT", "ULONG"))

    return ds
