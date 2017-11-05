var markers = {};
var map;
var quad;

function handle_new_position () {
	data = JSON.parse(this.responseText);
	data.map(function(item) {
		if (! markers.hasOwnProperty(item.title)) {
			marker = new google.maps.Marker({
				map: map,
				label: item.label,
				icon: icon,
				title: item.title,
			});

			markers[item.title] = marker;
		}

		marker = markers[item.title];
		marker.setPosition(item.position);

		if (item.hasOwnProperty('symbol')) {
			var icon = {
				path: google.maps.SymbolPath[item.symbol],
				scale: 10,
				strokeWeight: 4
			};

			if (item.hasOwnProperty('color')) {
				icon.fillColor = item.color;
				icon.fillOpacity = 1.0;
			}

			if (item.heading != null) {
				icon.rotation = item.heading;
			}

			marker.setIcon(icon);
		}

		if (item.center) {
			map.setCenter(item.position);
		}
	});
}

function update_position() {
	var req = new XMLHttpRequest();

	req.addEventListener('load', handle_new_position);
	req.open('GET', '/position');
	req.send();
}

function start_tracking() {
	setInterval(update_position, 100);
}

function initMap() {
	var pos;

	map = new google.maps.Map(document.getElementById('map'), {
		zoom: 20,
	});

	start_tracking();
}
