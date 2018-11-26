// switch.js

window.onload = function(){
  $('.form-control').on('change', function()
  {
    chartType = $("#chartType option:selected").val()
    chartData = $("#chartData option:selected").val()
    
    getData(url, chartType)
  })
  
}



// RUN
getData(url)