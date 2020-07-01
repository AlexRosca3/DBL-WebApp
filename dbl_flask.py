from flask import Flask, render_template, url_for, request,session,  send_from_directory, Response
from bokeh.io import push_notebook, show, output_notebook,curdoc
from bokeh.server.server import Server
from bokeh.embed import components, server_document
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.layouts import column, layout, row
from bokeh.models import Slider, Div, CheckboxGroup, MultiSelect, Select, FileInput, OpenURL, CustomJS, TapTool
from bokeh.plotting import figure, ColumnDataSource, show, output_file, save
from bokeh.resources import INLINE
from bokeh.palettes import Spectral4
from bokeh.transform import factor_cmap
from bokeh.models.callbacks import CustomJS
from bokeh.models.tools import HoverTool
from bokeh.models import ImageURL 
from bokeh.models.widgets import Tabs, Panel
from bokeh.models import FixedTicker, FuncTickFormatter
from bokeh.transform import dodge
from PIL import Image
import os
from os.path import dirname, join
from scipy.signal import savgol_filter
import numpy as np
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import datetime
import json
import plotly
import yfinance as yf
import plotly.graph_objs as go
from math import pi




app = Flask(__name__)
app.secret_key="DVISUALS"

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/vis")
def vis():
    return render_template('explain.html')


@app.route("/explain")
def explain():
    return render_template('explain.html')

@app.route("/scatter", methods=["POST", "GET"])
def scatter():
    
    file_name="all_fixation_data_cleaned_up.csv"
    if request.method == "POST":
        file = request.files["FileSelect"]
        if file.filename == '':
            print("No file to be found, We'll use the example dataset")
        else:
            print(file.filename)
            file_name=file.filename
        
        
    image_data= pd.read_excel("./static/images/MetroMapsEyeTracking/stimuli/resolution.xlsx", encoding='latin1')
    df_images= image_data.copy()

    image_name="01_Antwerpen_S1.jpg"
    image_location = "./static/images/MetroMapsEyeTracking/stimuli/{}".format(image_name)
    image= Image.open(image_location) #Opens the image location using the Image library
    image_width, image_height = image.size #image.size is width, height
    source_image = ColumnDataSource(dict(
            url = ["./static/images/MetroMapsEyeTracking/stimuli/{}".format(image_name)],
            x  = [0],
            y  = [image_height],
            w  = [image_width],
            h  = [image_height]
        ))
    
    Eyetracking_data = pd.read_csv(file_name, encoding='latin1', sep="\t")
    Eyetracking_data
    df = Eyetracking_data.copy()
    
    factor=0.05 #Factor to make non outlier Fixationtime values into the right radius size

    def stimuliListMaker(dataframe): #Makes a list with all stimulinames for 
        images=dataframe["StimuliName"].unique().copy()
        menu=[]
        for i in images:
            menu.append(i)
        return menu
        
    #Used for user selection
    def userListMaker(dataframe, stimuli):
        user_series = dataframe["user"][dataframe["StimuliName"] == stimuli].unique().copy()
        user_list=[]
        user_list.append("Everyone")
        for i in user_series:
            user_list.append(i)
        return user_list
    
#     def activeListMaker(user_list):
#         active_list=[]
#         for i in range(0, len(user_list)):
#             active_list.append(i)
#         return active_list
    
    def get_data(df, figure, users=["Everyone"]):
        if users[0] == "Everyone":
            X = df["MappedFixationPointX"][df["StimuliName"] == figure] #Select every x-coordinate from the chosen map
            Y = image_height - df["MappedFixationPointY"][df["StimuliName"] == figure] #Select every y-coordinate from the chosen map
            Fixationtime = df["FixationDuration"][df["StimuliName"] == figure] #Collect every fixationtime per timestamp for the chosen map
            Description = df["description"][df["StimuliName"] == figure] #Collects the descriptions from the database
            User = df["user"][df["StimuliName"] == figure] #Collects about which user this dot is.
            Radius = [] #Create empty list where the radius of the circle will be put in
            Color = [] #Create empty list where the right color for the circle will be assigned
            
        else:
            X = df["MappedFixationPointX"][(df["StimuliName"] == figure) & (df["user"] == users[0])] #Select every x-coordinate from the chosen map
            Y = image_height - df["MappedFixationPointY"][(df["StimuliName"] == figure) & (df["user"] == users[0])] #Select every y-coordinate from the chosen map
            Fixationtime = df["FixationDuration"][(df["StimuliName"] == figure) & (df["user"] == users[0])] #Collect every fixationtime per timestamp for the chosen map
            Description = df["description"][(df["StimuliName"] == figure) & (df["user"] == users[0])] #Collects the descriptions from the database
            User = df["user"][(df["StimuliName"] == figure) & (df["user"] == users[0])] #Collects about which user this dot is.
            Radius = [] #Create empty list where the radius of the circle will be put in
            Color = [] #Create empty list where the right color for the circle will be assigned
            
            for u in range(1, len(users)):
                X1 = df["MappedFixationPointX"][(df["StimuliName"] == figure) & (df["user"] == users[u])] #Select every x-coordinate from the chosen map
                Y1 = image_height - df["MappedFixationPointY"][(df["StimuliName"] == figure) & (df["user"] == users[u])] #Select every y-coordinate from the chosen map
                Fixationtime1 = df["FixationDuration"][(df["StimuliName"] == figure) & (df["user"] == users[u])] #Collect every fixationtime per timestamp for the chosen map
                Description1 = df["description"][(df["StimuliName"] == figure) & (df["user"] == users[u])] #Collects the descriptions from the database
                User1 = df["user"][(df["StimuliName"] == figure) & (df["user"] == users[u])] #Collects about which user this dot is.
                
                X = X.append(X1) #Add X1 to X
                Y = Y.append(Y1) #Add Y1 to Y
                Fixationtime = Fixationtime.append(Fixationtime1) #Add Fixationtime1 to Fixationtime
                Description = Description.append(Description1) #Add Description1 to Description
                User = User.append(User1) #Add User1 to User
                
                
                
        #This for loop will assign the radius and color to each circle
        for i in Fixationtime: 
            r= i * factor #radius = Fixationtime[i] * factor
            if r > 75: #If radius is above 75 px than make the radius 75 px and make the circle red. Else just make the circle blue.
                r=75
                Color.append("RED")
            else:
                Color.append("BLUE")
            Radius.append(r)
            
        data = dict(
            x= X,
            y= Y,
            fixationtime= Fixationtime,
            radius= Radius,
            user= User,
            description= Description,
            color = Color
        )

        return data #Returns a dictionary

    def make_plot(Tools, source):
        #The Hover-tool shows the Tooltips as shown here. The "@" stands for the data collected from the source
        Tooltips = [ 
            ("(x, y)", "(@x, @y)"),
            ("Fixation duration", "@fixationtime ms"),
            ("user", "@user"),
            #("description", "@description")
        ]

        #Creation of the figure
        plot = figure(x_range=(0,image_width), y_range=(0,image_height), tooltips=Tooltips, tools=Tools)
        
        
        image1 = ImageURL(url="url", x="x", y="y", w="w", h="h", anchor="top_left")
        plot.add_glyph(source_image, image1)
        # plot.image_url(url=[image_location], x=0, y=image_height, w=image_width, h=image_height)
        plot.circle(x='x', y='y', size='radius', color='color', alpha=0.2, source=source)
        return plot
    
    
    #The update functions:
#     def update_plot_stimuli(attr, old, new):
# #         try: #Will happen if dataset is selected, This is the case the first time because an example dataset is selected
#         image = new #Image is selected value
#         df = pd.read_csv(File_Input.filename, encoding='latin1', sep='\t')
#         data_new = get_data(df, image)             

#         #Change user selection to users of this plot stimuli and select the previously selected value if it exists.
        
#         user_select.options = userListMaker(df, image)
#         user_select.value = ["Everyone"]
#         source.data = data_new
# #         except: #Will happen if no dataset is selected.
# #             print("error")
        
    
    # def update_plot_dataset(attr, old, new):
    #     try: #Will happen if a dataset is selected
    #         dataframe = pd.read_csv(File_Input.filename, encoding='latin1', sep='\t')
            
    #         #Get the first image from the list to already show a map for the plot
    #         image_name = dataframe["StimuliName"][0] 
    #         image_location = "./static/images/MetroMapsEyeTracking/stimuli/{}".format(image_name)
    #         image= Image.open(image_location)
    #         image_width, image_height = image.size
            
    #         data_new = get_data(dataframe, image_name)
            
    #         #Change the stimuliSelection menu so that only the images from this dataset can be selected
    #         stimuliSelect.options=stimuliListMaker(dataframe)
    #         stimuliSelect.value=image_name
            
    #         #Change the user_select menu so that it only shows the users for this dataset with the first stimuli of the new dataset. Also resets the chosen value to "Everyone"
    #         user_select.options=userListMaker(dataframe, image_name)
    #         user_select.value=["Everyone"]
            
    #         source.data = data_new
        
    #     except: #Will happen if no dataset is selected
    #         print("error")
    
    #Potential user selection code
    # def update_plot_user(attr, old, new):
    #     active_list = new
    #     dataframe = pd.read_csv(File_Input.filename, encoding='latin1', sep='\t')
    #     stimuli = stimuliSelect.value
    #     data_new = get_data(dataframe, stimuli, active_list)
    #     source.data= data_new


    
    
    #Code needed to make stimuli selector 
    stimuliList = stimuliListMaker(df)
    stimuliSelect = Select(value=image_name, title='Stimuli', options=stimuliList)
    # stimuliSelect.on_change('value', update_plot_stimuli)
    

    #Code needed for file upload system
    # File_Input = FileInput(filename="all_fixation_data_cleaned_up.csv", accept=".csv")
    # File_Input.on_change('value', update_plot_dataset)
    
    
    Tools_vis1="pan,wheel_zoom, box_select, tap, reset, save"
    source = ColumnDataSource(data=get_data(df, image_name))
    
    #Code for the user selection
    user_list = userListMaker(df, image_name)
    user_select = MultiSelect(title="Users:", value=["Everyone"],
                        options=user_list ) #Don't forget to press shift or control (shift for everyone in between, control for selecting specific people) when selecting multiple users
    # user_select.on_change("value", update_plot_user)
    
    # fileInput_callback = CustomJS(args=dict(source=source, dataframe=ColumnDataSource(df), factor=factor, stimuli=stimuliSelect, users=user_select, FileInput=File_Input), code= 
    #     """
            
    #         //Collect every piece of data and that is given in the dictionary and put it in a variable
    #         var File_name=FileInput.filename;
    #         console.log(File_name);
    #         var oldDatadf = dataframe.data;
    #         var datasource = source.data;
    #         var userList = users.value;
    #         var newDatadf = atob(cb_obj.value);
    #         console.log(newDatadf);
            

    #         var f = factor;
    
    #         //Empty all lists that are in the source so that we can add new values to them
    #         datasource['x']=[];
    #         datasource['y']=[];
    #         datasource['fixationtime']=[];
    #         datasource['radius']=[];
    #         datasource['user']=[];
    #         datasource['description']=[];
    #         datasource['color']=[];


    #     """
    # )

    userSelect_callback = CustomJS(args=dict(source=source, dataframe=ColumnDataSource(df), source_image=source_image, factor=factor, stimuli=stimuliSelect), code=
        """
            //Collect every piece of data and that is given in the dictionary and put it in a variable
            var datadf = dataframe.data
            var datasource = source.data;
            var userList = cb_obj.value;
            var dataimagesource= source_image.data;

            var image_height = dataimagesource['h'][0];
            var image_width = dataimagesource['w'][0];

            var stimuli_name=stimuli.value;

            var f = factor;

            //Empty all lists that are in the source so that we can add new values to them
            datasource['x']=[];
            datasource['y']=[];
            datasource['fixationtime']=[];
            datasource['radius']=[];
            datasource['user']=[];
            datasource['description']=[];
            datasource['color']=[];

            for (var i = 0; i < datadf['StimuliName'].length; i++) { //MAYBE LOOK INTO PANDAS FOR JAVASCRIPT AS IT WOULD BE A LOT CLEANER THAN THIS 
                if (userList[0] == "Everyone") {
                    if (datadf['StimuliName'][i] == stimuli_name ) {
                        datasource['x'].push(datadf['MappedFixationPointX'][i])
                        datasource['y'].push(image_height - datadf['MappedFixationPointY'][i])
                        datasource['fixationtime'].push(datadf['FixationDuration'][i])

                        // Check if Radius that we want to give to the circle isn't to big. Else cap it to 75 px and make the circle RED
                        var Radius = datadf['FixationDuration'][i]*f;
                        if (Radius > 75) {
                            datasource['radius'].push(75)
                            datasource['color'].push("RED")
                        }
                        else {
                            datasource['radius'].push(Radius)
                            datasource['color'].push("BLUE")
                        }
                        
                        datasource['user'].push(datadf['user'][i])
                        datasource['description'].push(datadf['description'][i])
                    }
                } else {
                    for (var j=0; j < userList.length; j++){
                        if (datadf['StimuliName'][i] == stimuli_name && datadf['user'][i] == userList[j]) {
                            datasource['x'].push(datadf['MappedFixationPointX'][i])
                            datasource['y'].push(image_height - datadf['MappedFixationPointY'][i])
                            datasource['fixationtime'].push(datadf['FixationDuration'][i])

                            // Check if Radius that we want to give to the circle isn't to big. Else cap it to 75 px and make the circle RED
                            var Radius = datadf['FixationDuration'][i]*f;
                            if (Radius > 75) {
                                datasource['radius'].push(75)
                                datasource['color'].push("RED")
                            }
                            else {
                                datasource['radius'].push(Radius)
                                datasource['color'].push("BLUE")
                            }
                            
                            datasource['user'].push(datadf['user'][i])
                            datasource['description'].push(datadf['description'][i])
                        }
                    }
                }
            }
            source.change.emit();


        """
    )

    stimuliSelect_callback = CustomJS(args=dict(source=source, dataframe=ColumnDataSource(df), source_image=source_image, factor=factor, users=user_select), code=
        """
            users.value=["Everyone"]

            //Collect every piece of data and that is given in the dictionary and put it in a variable
            var datadf = dataframe.data
            var datasource = source.data;
            var userList = users;
            var dataimagesource= source_image.data;
            
            var new_stimuli = cb_obj.value;
            var location= ("./static/images/MetroMapsEyeTracking/stimuli/"+new_stimuli)
            dataimagesource['url'][0] = location    

            //Collect data on the new stimuli, so how wide is the corresponding image
            //COMMENT ON IMAGE SIZES: THE SIZE OF THE IMAGE DOESN'T CORRESPOND WITH THE DATAFRAME -_-. That's probably why we were also given a .csv File with the sizes of all the images. However this file is hard to make a correct dataframe from


            var new_image = new Image();
            new_image.src= location
            new_image.onload = function() {
                dataimagesource['h'][0] = this.height;
                dataimagesource['w'][0] = this.width;
            } 
            var image_height = dataimagesource['h'][0];
            var image_width = dataimagesource['w'][0];

            var f= factor;
            //console.log(userList[0]);
            //console.log(cb_obj.value);
            //console.log(datasource);
            //console.log(datadf);


            //Empty all lists that are in the source so that we can add new values to them
            datasource['x']=[];
            datasource['y']=[];
            datasource['fixationtime']=[];
            datasource['radius']=[];
            datasource['user']=[];
            datasource['description']=[];
            datasource['color']=[];
            

            //Add new values to the lists in the source
            for (var i = 0; i < datadf['StimuliName'].length; i++) { //MAYBE LOOK INTO PANDAS FOR JAVASCRIPT AS IT WOULD BE A LOT CLEANER THAN THIS 
                if (userList.value[0] == "Everyone") {
                    if (datadf['StimuliName'][i] == new_stimuli ) {
                        datasource['x'].push(datadf['MappedFixationPointX'][i])
                        datasource['y'].push(image_height - datadf['MappedFixationPointY'][i])
                        datasource['fixationtime'].push(datadf['FixationDuration'][i])

                        // Check if Radius that we want to give to the circle isn't to big. Else cap it to 75 px and make the circle RED
                        var Radius = datadf['FixationDuration'][i]*f;
                        if (Radius > 75) {
                            datasource['radius'].push(75)
                            datasource['color'].push("RED")
                        }
                        else {
                            datasource['radius'].push(Radius)
                            datasource['color'].push("BLUE")
                        }
                        
                        datasource['user'].push(datadf['user'][i])
                        datasource['description'].push(datadf['description'][i])
                        

                    }



                }
            }

            

            //https://appdividend.com/2019/04/11/how-to-get-distinct-values-from-array-in-javascript/
            //This function makes a list filter on unique values
            const unique = (value, index, self) => {
                return self.indexOf(value) === index
            }
            //Make a new List that will replace the old list with all users that look at the newly selected stimuli.
            var distinct_userList= ['Everyone'] 
            var distinctList=datasource['user'].filter(unique);
            for (var i=0; i < (distinctList.length); i++){
                //console.log(datasource['user'].filter(unique))
                distinct_userList.push(distinctList[i]);
            }
            users.options=distinct_userList;
            
            
            //source.change.emit() and source_image.change.emit() are needed to actually update the data that's in the source
            //users.options=["Everyone", "P1"];
            //users.value=["Everyone"]
            source.change.emit();
            source_image.change.emit();
        """)

    #JS_Callbacks, so basically calling an update function that runs on Javascript -_-
    stimuliSelect.js_on_change('value', stimuliSelect_callback)
    user_select.js_on_change('value', userSelect_callback)
    # File_Input.js_on_change('value', fileInput_callback)

    scatterplot = make_plot(Tools_vis1, source)
    controls = column(stimuliSelect, user_select)
    layout = row(scatterplot, controls)
    # curdoc.add_root(layout)
    script, div = components(layout, wrap_script=False)
    return render_template('scatterplot.html', script=script, div=div)


@app.route("/heatmap")
def heat():
    df = pd.read_csv("all_fixation_data_cleaned_up.csv", encoding='latin1', sep="\t")
    image_name = '01_Antwerpen_S1.jpg'
    image_location = "./static/images/MetroMapsEyeTracking/stimuli/{}".format(image_name)
    image= Image.open(image_location)
    img_width, img_height = image.size
    stimuli_list = df["StimuliName"].unique()
    user_list = df["user"].unique()
    series_stimuli = pd.Series(stimuli_list)
    series_users = pd.Series(user_list)

    #Creates a dictionary to get the data of a specific stimuli
    def get_data(df, figure):
        X = df["MappedFixationPointX"][df["StimuliName"] == figure].unique().tolist()
        Y = (img_height - df["MappedFixationPointY"][df["StimuliName"] == figure]).unique().tolist()
        Z = df["FixationDuration"][df["StimuliName"] == figure].unique().tolist()

        dict_of_fig = dict({
                    "visible": False,
                    "x": X,
                    "y": Y,
                    "z": Z,
                    "hovertemplate": "X: %{x}<br>" + "Y: %{y}<br>" + "Fixation Duration (ms): %{z}<br>" + "User: %{user}<br>",
                    "line": {"smoothing": 1.3},
                    "contours": {"showlines": False},
                    "ncontours": 30})
    
        return dict_of_fig

    #Creates the plot
    def create_plot(df, addNone = True):
        #empty plot
        fig = go.Figure()

        #Loops through all the stimuli and adds a trace to the empty plot for every single one
        for image in df["StimuliName"].unique().tolist():
            source = get_data(df, image)
            fig.add_trace(
                go.Histogram2dContour(source, name=image)
            )

        fig.update_layout(
            autosize=True,
            hovermode="closest",
            hoverdistance=-1,
            legend=dict(orientation='h'),
            xaxis=dict(autorange=True, range=[0, img_width], showgrid=False),
            yaxis=dict(autorange=True, range=[0, img_height], showgrid=False)
        )
        
        button_none = dict(label='None',
                            method = 'update',
                            args = [{'visible': False,
                                    'title': 'None',
                                    'showlegend': True}])

        def create_stimuli_dropdown(image):
            return dict(label = image,
                        method = 'update',
                        args = [{'visible': stimuli_list == image,
                                'title': image,
                                'showlegend': True}])

        fig.update_layout(
            updatemenus=[dict(
                active = 0,
                buttons = ([button_none] * addNone) + list(series_stimuli.map(lambda image: create_stimuli_dropdown(image))),
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.07,
                xanchor="left",
                y=1.25,
                yanchor="top"
            ),
                dict(
                    buttons=list([
                        dict(
                            args=["histfunc", "count"],
                            label="Count",
                            method="restyle"
                        ),
                        dict(
                            args=["histfunc", "avg"],
                            label="Average",
                            method="restyle"
                        ),
                        dict(
                            args=["histfunc", "sum"],
                            label="Sum",
                            method="restyle"
                        ),
                        dict(
                            args=["histfunc", "min"],
                            label="Minimum",
                            method="restyle"
                        ),
                        dict(
                            args=["histfunc", "max"],
                            label="Maximum",
                            method="restyle"
                        )       
                    ]),
                    direction="down",
                    pad={"r":10, "t":10},
                    showactive=True,
                    x=0.42,
                    xanchor="left",
                    y=1.25,
                    yanchor="top"
            ),
                dict(
                    buttons=list([
                        dict(
                            args=["histnorm", ""],
                            label="Standard",
                            method="restyle"
                        ),
                        dict(
                            args=["histnorm", "percent"],
                            label="Percent",
                            method="restyle"
                        ),
                        dict(
                            args=["histnorm", "probability"],
                            label="Probability",
                            method="restyle"
                        ),
                        dict(
                            args=["histnorm", "density"],
                            label="Density",
                            method="restyle"
                        ),
                        dict(
                            args=["histnorm", "probability density"],
                            label="Density Probability",
                            method="restyle"
                        )
                    ]),
                    direction="down",
                    pad={"r":10, "t":10},
                    showactive=True,
                    x=0.64,
                    xanchor="left",
                    y=1.25,
                    yanchor="top"
                )

        ])

        fig.update_layout(
                annotations=[
                    dict(text='Stimuli:', showarrow=False,
                    x=0, xref="paper", y=1.185, yref="paper", align="left"),
                    dict(text='Function:', showarrow=False,
                    x=0.37, xref="paper", y=1.185, yref="paper"),
                    dict(text='Norm:', showarrow=False,
                    x=0.6, xref="paper", y=1.185, yref="paper")
                ]
            )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return graphJSON
        
    plot = create_plot(df)
    return render_template('heatmap.html', plot=plot)

@app.route("/bar")
def bar():
    NameFile="All_fixation_data_cleaned_up.csv"
    df = pd.read_csv(NameFile, encoding = 'latin1', sep= '\t')

    orientation_xaxis=(6*pi/10) 

    df_sum= df[['StimuliName', 'description', 'user', 'FixationDuration']].groupby(['StimuliName', 'description', 'user'], as_index=False).sum()
    df_max= df[['StimuliName', 'description', 'user', 'FixationDuration']].groupby(['StimuliName', 'description', 'user'], as_index=False).max()
    df_mean= df[['StimuliName', 'description', 'user', 'FixationDuration']].groupby(['StimuliName', 'description', 'user'], as_index=False).mean()

    source_sum= ColumnDataSource(df_sum)
    source_max= ColumnDataSource(df_max)
    source_mean= ColumnDataSource(df_mean)

    Stimuli_list= df['StimuliName'].unique()
    Description_list= df['description'].unique()

    ToolBox= ['box_select', 'tap', 'pan', 'zoom_in', 'zoom_out', 'wheel_zoom', 'save', 'reset']
    ColorPalette= ['#20639B', '#3CAEA3', '#F6D55C', '#ED553B']


    #The creation of the plot, with the containing set of widgets
    plot_sum= figure(
        plot_height = 800, 
        plot_width= 1000,
        title = "Summation of Fixation Duration per Stimuli and User",
        x_range = Stimuli_list,
        y_axis_label= 'Fixation duration (sec)',
        tools = ToolBox )
    plot_sum.xaxis.major_label_orientation = orientation_xaxis


    plot_max= figure(
        plot_height = 800, 
        plot_width= 1000,
        title = "Maximum of Fixation Duration per Stimuli and User",
        x_range = Stimuli_list,
        y_axis_label= 'Fixation duration (sec)',
        tools = ToolBox )
    plot_max.xaxis.major_label_orientation = orientation_xaxis


    plot_mean= figure(
        plot_height = 800, 
        plot_width= 1000,
        title = "Mean of Fixation Duration per Stimuli and User",
        x_range = Stimuli_list,
        y_axis_label= 'Fixation duration (sec)',
        tools = ToolBox )
    plot_mean.xaxis.major_label_orientation = orientation_xaxis

    plot_sum.vbar(
        x="StimuliName",
        top= 'FixationDuration',
        width= 0.4,
        fill_color= factor_cmap('description', palette = ColorPalette, factors= Description_list),
        fill_alpha= 0.6,
        source= source_sum,
        selection_color= '#20639B',
        selection_alpha= 0.6,
        legend_field= 'description')

    plot_sum.legend.orientation = 'vertical'
    plot_sum.legend.location= 'top_right'
    plot_sum.toolbar.autohide = True
    tab_sum = Panel(child= plot_sum, title= 'Summation')


    plot_max.vbar(
        x="StimuliName",
        top= 'FixationDuration',
        width= 0.4,
        fill_color= factor_cmap('description', palette = ColorPalette, factors= Description_list),
        fill_alpha= 0.8,
        source= source_max,
        selection_color= '#F6D55C',
        selection_alpha= 0.6,
        legend_field= 'description')

    plot_max.legend.orientation = 'vertical'
    plot_max.legend.location= 'top_right'
    plot_max.toolbar.autohide = True
    tab_max = Panel(child= plot_max, title= 'Max') 


    plot_mean.vbar( 
        x="StimuliName",
        top= 'FixationDuration',
        width= 0.4,
        fill_color= factor_cmap('description', palette = ColorPalette, factors= Description_list),
        fill_alpha= 1.0,
        source= source_mean,
        selection_color= '#ED553B',
        selection_alpha= 0.6,
        legend_field= 'description')

    plot_mean.legend.orientation = 'vertical'
    plot_mean.legend.location= 'top_right'
    plot_mean.toolbar.autohide = True
    tab_mean = Panel(child= plot_mean, title= 'Mean')


    Taptools= plot_sum.select(type = TapTool)
    Tabben = Tabs(tabs= [tab_sum, tab_max, tab_mean])
    script, div = components(Tabben, wrap_script=False)
    return render_template('bar.html', script=script, div=div)

@app.route("/gazeplot", methods=["POST", "GET"])
def gazeplot():
    #CODE FOR THE GAZE STRIPE PLOT
    #The Gaze stripe plot has been made with the help of the following link: https://stackoverflow.com/questions/61908232/python-image-multiple-crops-with-pillow-and-grouped-and-displayed-in-a-row-with

    #Collecting the .csv file name from the POST method. If nothing has been posted yet, just take the example dataframe

    #KEEP IN MIND, IF THE FILE SELECTIO IS ON A DIFFERENT PAGE THEN MAKE SURE TO ADJUST THE CODE FOR SESSIONS SUCH THAT THE FIRST SESSION IS TERMINATED
    if "file_name" in session: file_name=session["file_name"]
    else: file_name="all_fixation_data_cleaned_up.csv" #Now it's fixed, later (via session) we will determine wether an example dataset is used or an already selected dataset

    if "image_name" in session: image_name=session["image_name"]
    else: image_name=""

    if "user_list" in session: user_list=session["user_list"]
    else: user_list=["Everyone"]

    def userListMaker(dataframe, stimuli):
        user_series = dataframe["user"][dataframe["StimuliName"] == stimuli].unique().copy()
        userlist=[]
        userlist.append({"name" : "Everyone"})
        for i in user_series:
            userlist.append({"name":i})
        return userlist

    def stimuliListMaker(dataframe): #Makes a list with all stimulinames for 
        images=dataframe["StimuliName"].unique().copy()
        menu=[]
        for i in images:
            menu.append({"name": i})
        return menu

    if request.method == "POST":
        file = request.files["FileSelect"]
        if file.filename == '':
            print("No file to be found, We'll use the example dataset")
            if  "Everyone" not in request.form.getlist("user_select"):
                user_list = request.form.getlist("user_select")
                session["user_list"] = user_list
            image_name = request.form.get("stimuli_select")
            session["image_name"]= image_name
        else:
            file_name=file.filename
            session["file_name"] =file_name
    
    #Make the dataframe
    Eyetracking_data = pd.read_csv(file_name, encoding='latin1', sep="\t")
    Eyetracking_data
    df = Eyetracking_data.copy()

    #Get first image name from the dataset
    if image_name == "":
        image_name=df["StimuliName"][0]

    if user_list == ["Everyone"]:
        df_stimuli = df[df["StimuliName"] == image_name].copy()
    else:
        df_stimuli = df[(df["StimuliName"] == image_name) & (df["user"].isin(user_list))].copy()

    image_location = './static/images/MetroMapsEyeTracking/stimuli/{}'.format(image_name)
    #Get the X and Y coordinates of the points where people looked at and put them in a list
    coordinates = list(df_stimuli[['MappedFixationPointX', 'MappedFixationPointY']].itertuples(index=False, name=None))
    picture_size = 100 #Can be any value, I liked this one. (Maybe make a potential slider for size?)

    #Open the image and convert is to an image with RedGreenBlueAlpha as it's color scheme
    image = Image.open(image_location).convert('RGBA')
    images = [] #Here will all cropped images be appended to.
    for x, y in coordinates:
        box = (x - picture_size / 2, y - picture_size / 2, x + picture_size / 2, y + picture_size / 2) #Takes a certain part of the image in accordance with the coordinate given and size of the "box" it makes. Keep in mind this line isn't an actual image but more like a placeholder
        images.append(np.array(image.crop(box)).view(np.uint32)[::-1]) #Append the part of the image into the images list.

    #Make a new column in df_stimuli called 'Image'
    df_stimuli['Image'] = images

    # There's probably a better method to populate `TimeCoord` which I don't know.
    df_stimuli = df_stimuli.sort_values('FixationDuration') #Sort the rows in df_stimuli by 'FixationDuration'
    df_stimuli['TimeCoord'] = 0 #Makes new column in df_stimuli called 'TimeCoord' (In what order did the user look at the set of coordinates) and sets all values to 0.
    for u in df_stimuli['user'].unique(): 
        user_df = (df_stimuli['user'] == u) 
        df_stimuli.loc[user_df, 'TimeCoord'] = np.arange(user_df.sum()) #Add for the currend user 'u' in df_stimuli the sum of all rows that this user possesses for this stimuli
    
     #This part replaces the values in the user colomn with a sort of zipped dictionary where the user is inserted and a list with the tuple describing the dimension of df_stimuli[0] (may be any number)
    user_coords = dict(zip(df_stimuli['user'].unique(), range(df_stimuli.shape[0]))) 
    df_stimuli['UserCoord'] = df_stimuli['user'].replace(user_coords)


    gaze_stripe_plot = figure(match_aspect=True)  #Really needs to be True in order for the squares to not becomes messed up.
    for r in [gaze_stripe_plot.xaxis, gaze_stripe_plot.xgrid, gaze_stripe_plot.ygrid]: #Basically just turn the xaxis, xgrid and y grid invisible as you don't need them
        r.visible = False

    # Manually creating a categorical-like axis to make sure that we can use `dodge` below.
    gaze_stripe_plot.yaxis.ticker = FixedTicker(ticks=list(user_coords.values())) 
    gaze_stripe_plot.yaxis.formatter = FuncTickFormatter(args=dict(rev_user_coords={v: k for k, v in user_coords.items()}),
                                        code="return rev_user_coords[tick];")


    source = ColumnDataSource(df_stimuli)
    img_size = 0.8
    gaze_stripe_plot.image_rgba(image='Image',
                x=dodge('TimeCoord', -img_size / 2), y=dodge('UserCoord', -img_size / 2),
                dw=img_size, dh=img_size, source=source)
    gaze_stripe_plot.rect(x='TimeCoord', y='UserCoord', width=img_size, height=img_size, source=source,
        line_dash='dashed', fill_alpha=0)

    layout = row(gaze_stripe_plot)



    script, div = components(layout, wrap_script=False)
    return render_template('about.html', script=script, div=div, userdata= userListMaker(df, image_name), stimulidata=stimuliListMaker(df), activeusersdata=user_list, activestimulidata=[image_name])

@app.route("/about")
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)