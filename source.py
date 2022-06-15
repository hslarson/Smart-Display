import time
import os
import random
import requests
import json 
import datetime


#Layers two arrays on top of each other
def layer(bottom, top, t_coords = (0,0), respect_spaces = False, center = False):
    #Initialize the output array
    out = []
    for row in range(len(bottom)):
        out.append([' ']*len(max(bottom, key=len)))

    #Copy the bottom array to the out array
    #It didn't work to use bottom.copy()
    for row in range(len(bottom)):
        for col in range(len(bottom[0])):
            out[row][col] = bottom[row][col]

    #Decide where to start drawing the top array
    #Using the center flag overwrites the x-coord
    if center:
        r_offset = t_coords[0]
        c_offset = (len(bottom[0]) - len(top[0])) // 2
    else:
        r_offset, c_offset = t_coords

    #Apply the top array at the specified coordinates,
    #Ignoring spaces if necessary
    for r in range(len(top)):
        for c in range(len(top[0])):
            if c < len(top[r]):
                if top[r][c] == ' ' and respect_spaces == False:
                    pass
                elif r_offset + r < len(out) and c_offset + c < len(out[0]):
                    out[r_offset + r][c_offset + c] = top[r][c]
                else:
                    #print("Layer Function Encountered an Out-of-Bounds Error!")
                    break
            else:
                continue
    
    return out


#Prints the values of a char array as one string
def showScreen(screen):

    rows = len(screen)
    for row in range(rows):
        print("".join(screen[row]))


#Searches shape.txt for a given shape
def getShape(shapeName):
    
    #Open the file containing the shapes
    shapeFile = open("/home/pi/Smart-Display/shapes.txt", 'r')
    if not shapeFile.readable():
        #print("Failed to Read the File!")
        return

    shape = []
    found = False

    #Search the file for the shape
    #Shapes are enclosed by two instances of the same name
    for line in shapeFile.readlines():
        if str(shapeName) in line:
            if not found:
                found = True
                continue
            else:
                break
        if found:
            shape.append(line.replace('\n', ''))
    
    #Close the file
    shapeFile.close()

    #Return shape if it could be found
    if not found:
        #print("Couldn't Find \'" + shapeName + "\'!")
        return
    else:
        return shape


#Takes an array and centers it
def centerShape(shapeArr, outSize, floor = -1, padding = -1):
    #Initialize the output
    out = []
    for row in range(outSize[0]):
        if padding == -1:
            out.append([' ']*outSize[1])
        else:
            out.append([' '] * (len(shapeArr[0]) + (2 * padding)))

    #Measure the shape
    shape_h = len(shapeArr)
    shape_w = len(max(shapeArr, key = len)) - 1 #for \n

    #Decide where to start drawing the shape
    if floor != -1:
        #The floor allows you to establish a shared lowest y-value (Should be useful for text)
        start_y = floor - shape_h
    else:
        start_y = (outSize[0] - shape_h) // 2

    #Apply the shape over the output array 
    #Let the layer function handle horizontal centering
    return layer(out, shapeArr, (start_y, 0), respect_spaces = True, center = True)


#Shows the current time and date
def getTime(init = False):

    #Get the current time
    current_time = time.localtime()
    current_time = [current_time.tm_mon, current_time.tm_mday, current_time.tm_wday, current_time.tm_hour, current_time.tm_min]

    #Convert 24-h time to 12-h time
    if current_time[3] > 12:
        current_time[3] -= 12
    elif current_time[3] == 0:
        current_time[3] = 12

    #Make minute 'n' appear as '0n' when n < 10
    minutes = str(current_time[4])
    if current_time[4] < 10:
        minutes = "0" + str(current_time[4])

    #Size constants
    numHeight  = 16
    dateHeight = 5

    #Build the time
    time_str = str(current_time[3]) + ":" + minutes
    temp_arr = []
    for char in time_str:
        charName = "Time" + char
        temp_arr.append(getShape(charName))

    #Format the time array
    time_arr = makeGrid( temp_arr, (1, len(temp_arr)), padding = (1, 2) )

    #Build the date
    #Add week day
    date_arr = []
    date_arr.append( getShape("Week" + str(current_time[2])) )

    #Add Month
    date_arr.append( getShape("Month" + str(current_time[0])) )
    
    #Add day of the month
    temp_arr = []
    for num in str(current_time[1]):
        temp_arr.append( getShape("Date" + str(num)) )
    date_arr.append( makeGrid(temp_arr, (1, len(temp_arr))) )

    #Format the date array
    date_arr = makeGrid(date_arr, (1, len(date_arr)), padding = (0, 1))
    
    #Clear out the old value of the global time array
    timeArray = []
    timeArray = [timeArray.append([]) for x in range(numHeight + dateHeight)]

    #Center the time/date arrays and layer them
    temp_arr = [time_arr, date_arr]
    timeArray = makeGrid( temp_arr,    (2, 1), padding = (0, -1) )
    timeArray = makeGrid( [timeArray], (1, 1), padding = (0, 1), border = ("thick", "None", "None"))

    #Return the new time array
    return timeArray


def makeGrid(data, grid_dims, out_size = (0,0), padding = (-1, -1), border = ("None", "None", "None")):
    
    #data - An array of arrays representing the contents of each cell
    #grid_dims - The number of cells per dimension (rows, cols)
    #out_size - The actual size of the output array. By default, it takes up as much space as necessary
    #padding - (top/bottom padding, left/right padding) Centered by default.
    #border - (outer border, inner horizontal border, inner vertical border)

    #If the input is an array of strings, convert it to an array of arrays
    if type(data[0][0]) == str:
        for cell in range(len(data)):
            for row in range(len(data[cell])):
                data[cell][row] = list(data[cell][row])

    #Define 3 different types of borders
    #(Vertical Symbol, Horizontal Symbol, Corner Symbol)
    border_styles = {
        "line" : ('|', '-', '+'),
        "thick": ('#', '=', '#'),
        "dots" : (':', '.', '.')
    }

    #If a specified border type doesn't math one of the types above, don't try to draw it
    temp = list(border)
    for i in range(len(temp)):
        if temp[i] not in border_styles:
            temp[i] = "None"
    border = tuple(temp)

    #Count the number of horizontal lines we need to draw (including borders)
    num_horiz_gridlines = 0
    if border[1] != "None":
        num_horiz_gridlines += grid_dims[0] - 1
    if border[0] != "None":
        num_horiz_gridlines += 2

    #Make the row sizes fixed if the out size is fixed
    row_sizes = []
    if out_size[0] > 0:
        row_sizes = [(out_size[0] - num_horiz_gridlines) // grid_dims[0]] * grid_dims[0]
    else:
        #Otherwise, for each row in the grid, create a subarray of all of the cells in that row
        for row in range(grid_dims[0]):
            sub_array = []
            for col in range(grid_dims[1]):
                if row * grid_dims[1] + col < len(data):
                    sub_array.append(data[row * grid_dims[1] + col])
                else:
                    break

            #For implicitly-sized arrays, set the row height to the tallest cell (including padding)
            cell_height = len(max(sub_array, key=len))
            if padding[0] > 0:
                cell_height += 2 * padding[0]

            row_sizes.append(cell_height)

    #Count the number of vertical lines we need to draw (including borders)
    num_vert_gridlines = 0
    if border[2] != "None":
        num_vert_gridlines += grid_dims[1] - 1 
    if border[0] != "None":
        num_vert_gridlines += 2

    #Make the column sizes fixed if the out size is fixed
    col_sizes = []
    if out_size[1] > 0:
        col_sizes = [(out_size[1] - num_vert_gridlines) // grid_dims[1]] * grid_dims[1]
    else:
        #For each column in the grid, create a sub array of all of the cells in that column
        for col in range(grid_dims[1]):
            sub_array = []
            for row in range(grid_dims[0]):
                if row * grid_dims[1] + col < len(data):
                    sub_array.append(data[row * grid_dims[1] + col])
                else:
                    break
            
            #For every cell in the subarray, find the longest row in that cell
            #Then find the maximum out of those values
            longest = 0
            for cell in sub_array:
                if padding[1] > 0 and len(max(cell, key=len)) + 2 * padding[1] > longest:
                    longest = len(max(cell, key=len)) + 2 * padding[1]
                
                elif padding[1] <= 0 and len(max(cell, key=len)) > longest:
                    longest = len(max(cell, key=len))

            #Assign longest (including padding) to array
            col_sizes.append(longest)
    
    #Calculate the physical dimensions of the grid
    grid_height = num_horiz_gridlines + sum(row_sizes)
    grid_width  = num_vert_gridlines  + sum(col_sizes)

    #Initialize a blank array with those dimensions
    out = []
    for row in range(grid_height):
        out.append([' ']*grid_width)
    
    #Draw horizontal lines if necessary
    index = 0
    row_sizes_copy = row_sizes.copy()
    if border[1] != "None":
        while index < grid_height:
            #Skip the top border for now
            if index == 0 and border[0] != "None":
                index = 1
                continue
            
            #Jump to the index of the horizontal lines we we need to draw
            index += row_sizes_copy.pop(0)

            #Skip the bottom border as well
            if index < grid_height - 1:
                out[index] = [border_styles.get(border[1])[1]]*grid_width
            else:
                break
            
            index += 1 #Skip to the next row
    
    #Draw vertical lines if necessary
    index = 0
    col_sizes_copy = col_sizes.copy()
    if border[2] != "None":
        while index < grid_width:
            #Skip the left border for now
            if index == 0 and border[0] != "None":
                index = 1
                continue
            
            #Jump to the index of the vertical lines we we need to draw
            index += col_sizes_copy.pop(0)

            #Skip the right border
            if index < grid_width - 1:
                for row in range(grid_height):
                    out[row][index] = border_styles.get(border[2])[0]
            else:

                break
            index += 1 #Jump to the next column
    
    #Draw outer border if necessary
    if border[0] != "None":
        #Top border + Corners
        out[0]              = [border_styles.get(border[0])[2]] + [border_styles.get(border[0])[1]]*(grid_width - 2) + [border_styles.get(border[0])[2]]
        
        #Bottom Border + Corners
        out[grid_height -1] = [border_styles.get(border[0])[2]] + [border_styles.get(border[0])[1]]*(grid_width - 2) + [border_styles.get(border[0])[2]]
        
        for row in range(1, grid_height - 1):
            #Left Border
            out[row][0]              = border_styles.get(border[0])[0]

            #Right Border
            out[row][grid_width - 1] = border_styles.get(border[0])[0]


    #Position the data in the cells
    for cell in range(min(len(data), grid_dims[0] * grid_dims[1])):
        #Compute the starting coordinates
        #Start by summing the widths/heights of prior rows
        #Add one for borders, add one for every prior cell if there are gridlines
        start_y = sum(row_sizes[:(cell //  grid_dims[1] if cell // grid_dims[1] > 0 else 0)]) + (1 if border[0] != "None" else 0) + (cell //  grid_dims[1] if border[1] != "None" else 0)
        start_x = sum(col_sizes[:(cell %   grid_dims[1] if cell %  grid_dims[1] > 0 else 0)]) + (1 if border[0] != "None" else 0) + (cell %   grid_dims[1] if border[2] != "None" else 0)

        #Measure the cell
        max_height = row_sizes[cell //  grid_dims[1]]
        max_width  = col_sizes[cell %   grid_dims[1]]

        #Measure the data
        cell_height = len(data[cell]) 
        cell_width  = len(max(data[cell], key=len))

        #Trim the height of the data to max height minus padding
        if cell_height + (2 * padding[0] if padding[0] > -1 else 0) > max_height:
            data[cell] = data[cell][: max_height - (2 * padding[0] if padding[0] > -1 else 0)]
        
        #Trim the width of the data to the max width minus padding
        if cell_width  + (2 * padding[1] if padding[1] > -1 else 0) > max_width:
            for row in range(len(data[cell])):
                data[cell][row] = data[cell][row][:max_width - (2 * padding[1] if padding[1] > -1 else 0)]

        #Align the data within a cell-sized array then apply that array to the grid
        temp = centerShape(data[cell], (max_height, max_width), (len(data[cell]) + padding[0] if padding[0] > -1 else -1), (padding[1] if padding[1] > -1 else -1))
        out = layer(out, temp, (start_y, start_x))

    return out


#Shows the current weather and 5-day forecast
def getWeather(init = False):
    global weatherArray
    global weatherClock
    
    #Initialize the clock if necessary, this will also populate the weather array
    if init:
        weatherClock = time.monotonic()
        weatherArray = []
    
    #Swaps the hourly and daily forecasts on a preset interval
    swap_interval    = 10 #seconds
    def showOutput(blocks, start, swap_frequency):
        if (time.monotonic() - start) // swap_frequency % 2 == 0:
            return makeGrid([blocks[0], blocks[1]], (2, 1), padding =(0, -1), border=("thick", "thick", "thick"))
        else:
            return makeGrid([blocks[0], blocks[2]], (2, 1), padding =(0, -1), border=("thick", "thick", "thick"))
    
    #Only refreshes the weather data on a preset interval to improve performance
    refresh_interval = 900 #seconds
    if not init and (time.monotonic() < weatherClock + refresh_interval):
        return showOutput(weatherArray, weatherClock, swap_interval)
    else:
        weatherClock = time.monotonic() #Everything below is in an implied else statement

    #Determines what shape is drawn for every possible weather code
    weather_reference = {
        "Clouds" : "WeatherClouds",
        "Mist"   : "WeatherClouds",
        "Smoke"  : "WeatherClouds",
        "Haze"   : "WeatherClouds",
        "Dust"   : "WeatherClouds",
        "Fog"    : "WeatherClouds",
        "Sand"   : "WeatherClouds",
        "Ash"    : "WeatherClouds",
        "Drizzle": "WeatherRain",
        "Rain"   : "WeatherRain",
        "Squall" : "WeatherRain",
        "Tornado": "WeatherRain",
        "Snow"   : "WeatherSnow",
        "Thunderstorm": "WeatherLightning"
    }

    #Construct the URL
    base_url = "http://api.openweathermap.org/data/2.5/onecall?"
    lat = weather_latitude
    lon = weather_longitude
    api_key = weather_api_key
    
    complete_url = base_url + "lat=" + lat + "&lon=" + lon + "&units=imperial" + "&appid=" + api_key

    #Call the API (Avoiding network errors)
    try:
        response = requests.get(complete_url) 
    except:
        return showOutput(weatherArray, weatherClock, swap_interval)
    
    x = response.json()
    
    #Create the current conditions array
    current_conditions = []
    current = x["current"]

    #If the temperature is less than freezing, set the icon to the snowflake
    current_symbol = []
    if current["temp"] < 32:
        current_symbol = getShape("WeatherSnow")

    #If the the weather is clear, display a sun if it's daytime or a moon if it's nighttime
    elif current["weather"][0]["main"] == "Clear":
        if time.time() > current["sunrise"] and time.time() < current["sunset"]:
            current_symbol = getShape("WeatherSun")
        else:
            current_symbol = getShape("WeatherMoon")
    
    #Otherwise, show the symbol dictated by the dictionary
    else:
        current_symbol = getShape( weather_reference.get(current["weather"][0]["main"]) )
    
    #Begin constructing the current info panel 
    current_info = []

    #Display the current temperature
    current_info.append(["Temperature: "]) 
    current_info.append([str(round(current["temp"])) + " F"])

    #Display the "feels like" temperature
    current_info.append(["Feels Like: "])
    current_info.append([str(round(current["feels_like"])) + " F"])

    #Display the humidity
    current_info.append(["Humidity: "])
    current_info.append([str(current["humidity"]) + "%"])
    
    #Change the wind direction in degrees into to cardinal directions and display the wind info
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    temp = round(current["wind_deg"] / (360. / len(dirs)))
    current_info.append(["Wind: "])
    current_info.append([str(current["wind_speed"]) + "mph " + dirs[temp % len(dirs)]])

    #Get the description of the current weather
    description = [ list(current["weather"][0]["description"].title().strip()) ]

    #Construct the panel by making a grid for the temp, feels like, humidity, and wind info
    temp_arr = makeGrid(current_info, (4, 2), padding=(0, 0), border=("None", "dots", "None"))

    #Add the description to the panel as a "header"
    temp_arr = makeGrid([description, temp_arr], (2, 1), padding=(0, 1), border=("None", "line", "None"))
    
    #Add the symbol on the left side of the grid we just made
    current_conditions = makeGrid([current_symbol, temp_arr], (1, 2), out_size = (15, 0), padding = (-1, 3), border=("None", "None", "line"))

    #Begin constructing the hourly conditions
    hourly_conditions = []
    cell_width = 8 #Kinda hacky, should debug the grid system

    for hr in x["hourly"][1:13]:
        temp_arr = []
        #Start by getting the time
        t = datetime.datetime.fromtimestamp(hr["dt"]).hour
        ampm = "am"
        if t > 12:
            t -= 12
            ampm = "pm"
        elif t == 0:
            t = 12

        temp_arr.append( (str(t) + " " + ampm).center(cell_width) )
        temp_arr.append( "-"*cell_width )

        #Get the conditions
        temp_arr.append( hr["weather"][0]["main"].center(cell_width) )

        #Get the temperature
        temp_arr.append( " " )
        temp_arr.append( (str(round(hr["temp"])) + " F").center(cell_width) )

        #Add the cell to the array
        hourly_conditions.append( temp_arr )

    #Make the grid for the hourly conditions
    hourly_conditions = makeGrid(hourly_conditions, (2, 6), padding=(1, 1), border=("None", "dots", "dots"))
    
    #Begin constructing the 5-day forecast
    daily_conditions = []
    weekdays = ["Monday:", "Tuesday:", "Wednesday:", "Thursday:", "Friday:", "Saturday:", "Sunday:"]
    cell_width = 10 #Kinda hacky, should debug the grid system
    tomorrow = True
    
    for day in x["daily"][1:6]:
        temp_arr = []

        #Add the day
        if tomorrow:
            tomorrow = False
            t = "Tomorrow:"
        else:
            t = weekdays[datetime.datetime.fromtimestamp(day["dt"]).weekday()]
        temp_arr.append( t.center(cell_width) )
        temp_arr.append( "-"*cell_width )
        temp_arr.append(" ")

        #Add conditions
        temp_arr.append( day["weather"][0]["main"].center(cell_width) )
        temp_arr.append(" ")

        #Add Average Temperature
        temp_arr.append( ("Temp: " + str(round(day["temp"]["day"]))).center(cell_width) )
        temp_arr.append( " ")

        #Add the high/low temps
        temp_arr.append( ("High: " + str(round(day["temp"]["max"]))).center(cell_width) )
        temp_arr.append( ("Low:  " + str(round(day["temp"]["min"]))).center(cell_width) )

        daily_conditions.append( temp_arr )

    #Construct the 5-day forecast
    daily_conditions = makeGrid(daily_conditions, (1, 5), padding=(2, 1), border=("None", "None", "line"))

    #Update the global variable
    weatherArray = [current_conditions, hourly_conditions, daily_conditions]
    
    #Return an array if init is false
    if not init:
        return showOutput(weatherArray, weatherClock, swap_interval)


#Loads an RSS feed with important news
def getNews(init = False):
    global newsRefreshClock
    global newsClock
    global newsDisplayArray
    global newsMainFeed
    global newsRawArray
    global numCalls

    #Wraps the text to fit a given length, adding dashes when necessary
    def textWrap(text, length):
        out = []
        while len(text) > length:
            #If the next character is not a space..
            #Find the last space and append everything before that
            if text[length] != " ":
                temp = text[:length].rpartition(" ")
                out.append(temp[0])
                text = temp[2] + text[length:] #Add any remaining characters back to the main string
            
            #Otherwise, simply add everything before the space to the out array
            #And leave everything after the space as is
            else:
                out.append(text[:length])
                text = text[length + 1:]

        #Add any of the leftovers to the out array
        out.append(text)
        return out

    #Initialize clock
    if init:
        newsRefreshClock = time.monotonic()
        newsClock = time.monotonic()
        newsDisplayArray = []
        newsRawArray     = []
        newsMainFeed     = []
        numCalls = 0
        
    #Build URL
    base_url = 'http://newsapi.org/v2/top-headlines?country=us&apiKey='
    api_key  = news_api_key
    url  = base_url + api_key

    refresh_interval = 600 #Call the API (at most) every x seconds
    out_length = 8         #How many stories to render at once
    if init or len(newsRawArray) <= out_length:

        #If the refresh cooldown is over, refresh the feed
        if init or time.monotonic() > newsRefreshClock + refresh_interval:
            
            newsRefreshClock = time.monotonic() #Reset the clock
            
            #Try to call the API (throws error w/o internet connection)
            try:
                numCalls += 1
                newsMainFeed = requests.get(url).json()["articles"]
            except:
                pass
        
        #Pass the new feed (Or possibly the old feed if the internet is out 
        #or the cooldown period has not passed) to the raw news feed
        newsRawArray = newsMainFeed.copy() + newsRawArray

    #Every x seconds, re-render the raw array
    rotation_speed = 8 #seconds
    if not init and time.monotonic() < newsClock + rotation_speed:
        return newsDisplayArray
    else:
        newsClock = time.monotonic() #Refresh the clock
        newsRawArray.pop()           #Remove the last story

    #Some Array constants
    out_array_dims = (30, 80)

    #Draw the last x stories in the array
    newsDisplayArray.clear()
    for story in newsRawArray[-1 * out_length:]:
        temp_arr = []

        #Add the Headline
        title = story["title"].strip()
        if " - " in title:
            title = title.rpartition(" - ")[0]

        temp_arr.extend( textWrap(title, out_array_dims[1]) )
        temp_arr.append("")

        #Add the source
        temp_arr.append( "Source: " + story["source"]["name"] )

        #Add the story to the output array
        newsDisplayArray.append( temp_arr )

    #Make the main grid
    newsDisplayArray = makeGrid(newsDisplayArray, (out_length, 1), padding=(0,1), border=("None", "dots", "None"))
    
    #Trim and frame the grid
    newsDisplayArray = makeGrid([newsDisplayArray], (1, 1), (out_array_dims[0], 0), border=("thick", "None", "None"))
    return newsDisplayArray


#Creates the base layer with cutout for widgets and random noise as well
def getBackground(current = []):
    
    symbols = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','!','"','#','$','%','&','\'','(',')','*','+',',','-','.','/',':',';','<','=','>','?','@','[','\\',']','`','^','_','{','|','}','~']
    if len(current) == 0:
        noise = []
        for row in range(ROWS):
            noise.append( random.choices(symbols, k=COLUMNS) )
        
        return noise

    else:
        #Choose a few characters to randomize
        for row in range(ROWS):
            bool_arr = random.choices([True, False], weights=(0.002, 0.998), k = COLUMNS)
            char_arr = random.choices(symbols, k = COLUMNS)

            for col in range(COLUMNS):
                if bool_arr[col]:
                    current[row][col] = char_arr[col]
        
        return current



# Load Secrets File
file = open("/home/pi/Smart-Display/secrets.json")
if file.readable:
    contents = json.load(file)
    
    weather_latitude = contents["weather_latitude"]
    weather_longitude = contents["weather_longitude"]
    weather_api_key = contents["weather_api_key"]
    news_api_key = contents["news_api_key"]
    
    file.close()
else:
    raise Exception("Failed to Load Secrets File")


#Array size constants
ROWS = 95
COLUMNS = 108

#Size Constants
time_height    = 25
weather_height = 32
news_height    = 30

y_spacing = (ROWS - (time_height + weather_height + news_height)) // 4

time_y_spacing    = 1 * y_spacing
weather_y_spacing = 2 * y_spacing + time_height
news_y_spacing    = 3 * y_spacing + (time_height + weather_height)

#Time Constants
clock_interval = 10
end = 23 #11:00pm

#Main loop
startup = True
numCalls = 0
while time.localtime().tm_hour < end:
    if startup:
        startup = False

        #Initialize Modules
        getTime(init = True)
        getWeather(init = True)
        getNews(init=True)

        #Play the opening animation
        background_arr = getBackground()

        time_arr       = ['']
        weather_arr    = []
        news_arr       = []


    #Generate all of the widgets
    background_arr = getBackground(background_arr)
    time_arr       = getTime()
    weather_arr    = getWeather()
    news_arr       = getNews()

    #Stack all of the layers
    new_screen = []
    new_screen = background_arr.copy()
    new_screen = layer(new_screen, time_arr,    (time_y_spacing,  0),   respect_spaces = True, center = True)
    new_screen = layer(new_screen, weather_arr, (weather_y_spacing, 0), respect_spaces = True, center = True)
    new_screen = layer(new_screen, news_arr,    (news_y_spacing, 0),    respect_spaces = True, center = True)

    # Draw Screen
    showScreen(new_screen)
    
    #Wait
    time.sleep(clock_interval)


print( "NUMBER OF NEWS API CALLS: " + str(numCalls))
