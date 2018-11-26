var CLIENT_ID = ""
var SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"];
var key = ""
var url = "https://spreadsheets.google.com/feeds/list/" + key + "/od6/public/values?alt=json";

var chartType = "pie"
var chartData = "gsx$keywords"


// START HERE; Fetches data from googlesheets API
function getData(url, chartMap = "chart")
{
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() 
  {
      if (xhttp.readyState == 4 && xhttp.status == 200 && chartMap != "map") 
      {
        console.log( JSON.parse(xhttp.responseText).feed.entry )
        counts = getCounts(JSON.parse(xhttp.responseText).feed.entry, chartData)
        chartCounts(counts, chartType)
      }
      if (xhttp.readyState == 4 && xhttp.status == 200 && chartMap == "map")
      {
        initMap(JSON.parse(xhttp.responseText).feed.entry)
      }
  }
  xhttp.open("GET", url, true);
  xhttp.send();
}


// Input variable, output UNIQUE COUNTS for each value of input
function getCounts(dat, by)
{
  var output = {};
  for (var i = 0, l = dat.length; i < l; i++)
  {
    b = dat[i];
    output[b[by]["$t"]] = (output[b[by]["$t"]] || 0) + 1;
  }
  console.dir( output );
  return output 
}


// CHART processed data
function chartCounts(counts, chartType)
{
  $('#myChart').remove();
  $('#content').empty()
  $('#content').append('<canvas id="myChart"><canvas>');
  ctx = document.getElementById("myChart");

  labels = [];
  values = [];
  var ctx = document.getElementById("myChart");

  for (entry in counts)
  {
    values.push(counts[entry])
    labels.push(entry)
  }
  var data = {
    labels: labels,
    datasets: [{
      data: values
    }]
  };
  var barChart = new Chart(ctx, {
    type: chartType,
    data: data,
    options:
    {
        responsive: true,
        maintainAspectRatio: false,
        legend: {
          display: false
        },
        scales:
        {
            xAxes: [{
                display: false
            }]
        }
    }
  });

};


function initMap(dat)
{
  $('#content').empty()
  $('#content').append('<div id = "map" style = "height:300px; width: 100%"></div>');
  
  var geojson = toGeojson(dat)
  var map = L.map('map')
  map.setView([50,-90], 5)
  //map.setMaxBounds([[60,-115],[38,-65]])
  
  L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
	  attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
	  subdomains: 'abcd',
	  maxZoom: 19
  }).addTo(map)

  L.geoJSON(geojson, {onEachFeature: onEachFeature}).addTo(map)


}

function toGeojson(dat)
{
  geojson = []
  for (i=0; i < dat.length; i++)
  {
    point = dat[i]
    if (point['gsx$relevantlocationlat']['$t'] == "Cant Find" || point['gsx$relevantlocationlong']['$t'] == "Cant Find"  || point['gsx$relevantlocationlat']['$t'] == 0 || point['gsx$relevantlocationlong']['$t'] == -85.3232139)
    {
      continue
    }
    
    console.log(point)
    feature = {}
    
    feature.properties = {}
    feature.properties.instrument = point['gsx$instrument']['$t']
    feature.properties.commenthref = point['gsx$commenthref']['$t']
    feature.properties.relevantlocationname = point['gsx$relevantlocationname']['$t']
    feature.properties.noticehref = point['gsx$noticehref']['$t']
    feature.properties.proponent = point['gsx$proponent']['$t']
    feature.properties.keywords = point['gsx$keywords']['$t']
    feature.properties.decisionloaded = point['gsx$decisionloaded']['$t']
    feature.properties.proposalloaded = point['gsx$proposalloaded']['$t']
    
    feature.geometry = {
      "type": "Point", 
      "coordinates": [ point['gsx$relevantlocationlong']['$t'], point['gsx$relevantlocationlat']['$t'] ]
    }
    feature.type = "Feature"
    console.dir(feature)
    geojson.push(feature)
  }
  return geojson
}

function onEachFeature(feature, layer)
{
  if( feature.properties.commenthref === "" ) {decision = ''}
  else{decision = "<p><a style = 'color: white' class = 'btn btn-primary' href = 'https://www.ebr.gov.on.ca"+feature.properties.commenthref.replace("¬", "&amp;not").replace("&not", "&amp;not").replace("&", "&amp;")+"'>Submit Comment to Ministry</a></p>"}
  layer.bindPopup(
    '<b align = "center">' + feature.properties.relevantlocationname + '</b>'
    + '<p>' + feature.properties.instrument + '</p>'
    + '<p> Proposed By: ' + feature.properties.proponent + '</p>'
    + '<p> Proposed On: ' + feature.properties.proposalloaded + '</p>'
    + decision
    + '<p> Keywords: ' + feature.properties.keywords + '</p>'
    + "<p><a style = 'color: white' class = 'btn btn-primary' href = '"+feature.properties.noticehref.replace("¬", "&amp;not")+"'>Learn More</a></p>",
    {'maxHeight': '150'}
    
  )
}
