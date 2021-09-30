# sol-view
## A GUI to facilitate the plot of data stored in hdf5 files

To begin with, install all dependencies:

```
pip install -r requirements.txt
```

To launch the GUI, just run sol_view.py:

```
./sol_view.py
```

![sol-view main screen.](images/main_screen.png "sol-view main screen")

Press ctrl+O to open a file or go to to File > Open File.

![Open file dialog.](images/open_dialog.png "Open file dialog")

After opening a file, the plot window will be shown. Use the checkboxes to select the things you want to see in the graphic.

![Plot window.](images/single_file.png "Plot window")

You can also open several files in the same plot. To do that, hold ctrl and select the files you want:

![Select several files.](images/open_multi_files.png "Select several files")

![Plot with several files.](images/multi_files.png "Plot with several files")

Select a displayed curve to get statistics from it:

![Get statistics from a curve.](images/get_stats.png "Get statistics from a curve")

There is an added functionality that can perform derivative in all displayed curves. Note that new functionalities can be implemented.

![Derivative of all curves.](images/derivative.png "Derivative of all curves")