import tkinter as tk
import tkinter.font
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
from dataclasses import dataclass
import time


@dataclass
class Target:
    id: int
    x: int
    y: int
    r: int
    created_at: float


@dataclass
class Measurement:
    elapsed: float
    distance: float
    width: int


class Fritts:

    def init_gui(self):
        self.window = tk.Tk()
        self.window.title("Fritts Measurer")

        self.window.rowconfigure(0, minsize=40)
        self.window.rowconfigure(1)
        self.window.columnconfigure(0)
        self.window.columnconfigure(1)

        font = tkinter.font.Font(size=14)
        self.label = tk.Label(self.window, font=font,
            text="Please click the shapes as fast as you can.")
        self.label.grid(row=0, column=0, sticky=tk.W)

        self.but_finish = tk.Button(
            self.window, text="Finish!", font=font, command=self.finish)
        self.but_finish.grid(row=0, column=1, sticky=tk.N+tk.S+tk.E)

        self.canv = tk.Canvas(
            self.window, width=self.sizeX, height=self.sizeY)
        self.canv.grid(row=1, column=0, columnspan=2)
        self.canv.bind("<Button-1>", self.click_shape)

    def __init__(self, sizeX, sizeY):
        self.sizeX, self.sizeY = sizeX, sizeY
        self.init_gui()
        self.measurements = []
        self.target = self.draw_random_circle()
        self.before_x = self.target.x
        self.before_y = self.target.y

    def draw_random_circle(self):
        r = int(np.random.weibull(1.2) * 60) + 3
        x = np.random.randint(0, self.sizeX-2*r)
        y = np.random.randint(0, self.sizeY-2*r)
        return Target(
            self.canv.create_oval(x,y,x+2*r,y+2*r, fill="gray", outline="gray", width=1),
            x+r,y+r,r,
            time.perf_counter())

    def is_inside(self, event):
        canv = event.widget
        x = canv.canvasx(event.x)
        y = canv.canvasy(event.y)
        d = (self.target.x - x)**2 + (self.target.y - y)**2
        rsq = self.target.r**2
        return d <= rsq

    def click_shape(self, event):
        if not self.is_inside(event):
            return
        elapsed = time.perf_counter() - self.target.created_at
        distance = (self.target.x - self.before_x)**2 + (self.target.y - self.before_y)**2
        self.measurements.append(Measurement(
            elapsed, distance**.5, self.target.r*2
        ))
        self.before_x = event.widget.canvasx(event.x)
        self.before_y = event.widget.canvasx(event.y)
        self.canv.delete(self.target.id)
        self.target = self.draw_random_circle()

    def finish(self):
        self.window.destroy()
        p = Plotter(self.measurements[1:], self.window)
        p.fit()
        p.plot()
        self.window.quit()



class Plotter:
    def __init__(self, meas, window):
        elapsed = np.array([m.elapsed for m in meas])
        distance = np.array([m.distance for m in meas])
        width = np.array([m.width for m in meas])

        self.elapsed = elapsed
        self.distance = distance
        self.width = width

        self.window = window

    def plot(self):
        fig = plt.figure()
        ax = plt.axes(projection='3d')
        ax.set_xlabel('distance')
        ax.set_ylabel('width')
        ax.set_zlabel('elapsed')
        distance = self.distance
        width = self.width
        elapsed = self.elapsed

        ax.scatter3D(distance, width, elapsed, c=elapsed, cmap='viridis')


        di = np.linspace(min(distance), max(distance), 15)
        wi = np.linspace(min(width), max(width), 80)
        di, wi = np.meshgrid(di, wi)
        el = self.fitts((di, wi), self.a, self.b)
        ax.plot_surface(di, wi, el, cstride=1, rstride=1, alpha=.5, cmap='Greens')

        ax.view_init(15, 6)

        plt.show()
        
    
    @staticmethod
    def fitts(distance_width, a, b):
        distance, width = distance_width
        return a + b * np.log2(np.divide(distance, width)+1)

    def fit(self):
        popt, _ = curve_fit(self.fitts, (self.distance, self.width), self.elapsed)
        self.a = popt[0]
        self.b = popt[1]


if __name__ == "__main__":
    f = Fritts(1000, 800)
    f.window.mainloop()
    
    