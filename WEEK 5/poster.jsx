function c(s) { return charIDToTypeID(s); }
function s(str) { return stringIDToTypeID(str); }

function colorStop(r, g, b, percent) {
    var rgb = new ActionDescriptor();
    rgb.putDouble(c("Rd  "), r);
    rgb.putDouble(c("Grn "), g);
    rgb.putDouble(c("Bl  "), b);
    var stop = new ActionDescriptor();
    stop.putObject(c("Clr "), c("RGBC"), rgb);
    stop.putEnumerated(c("Type"), c("Clry"), c("UsrS"));
    stop.putInteger(c("Lctn"), Math.round(percent / 100 * 4096));
    stop.putInteger(c("Mdpn"), 50);
    return stop;
}

function opacityStop(percent) {
    var stop = new ActionDescriptor();
    stop.putUnitDouble(c("Opct"), c("#Prc"), 100);
    stop.putInteger(c("Lctn"), Math.round(percent / 100 * 4096));
    stop.putInteger(c("Mdpn"), 50);
    return stop;
}

// Gradient fill layer, bottom (0%) to top (100%).
function addSunsetGradient() {
    var colors = new ActionList();
    colors.putObject(c("Clrt"), colorStop(255, 214, 110, 0));    // glowing horizon
    colors.putObject(c("Clrt"), colorStop(255, 132, 62, 30));    // orange
    colors.putObject(c("Clrt"), colorStop(222, 70, 104, 58));    // pink
    colors.putObject(c("Clrt"), colorStop(112, 44, 130, 82));    // purple
    colors.putObject(c("Clrt"), colorStop(38, 22, 82, 100));     // deep dusk sky

    var opacity = new ActionList();
    opacity.putObject(c("TrnS"), opacityStop(0));
    opacity.putObject(c("TrnS"), opacityStop(100));

    var grad = new ActionDescriptor();
    grad.putString(c("Nm  "), "Sunset");
    grad.putEnumerated(c("GrdF"), c("GrdF"), c("CstS"));
    grad.putDouble(c("Intr"), 4096);
    grad.putList(c("Clrs"), colors);
    grad.putList(c("Trns"), opacity);

    var fill = new ActionDescriptor();
    fill.putUnitDouble(c("Angl"), c("#Ang"), 90);
    fill.putEnumerated(c("Type"), c("GrdT"), c("Lnr "));
    fill.putObject(c("Grad"), c("Grdn"), grad);

    var layer = new ActionDescriptor();
    layer.putString(c("Nm  "), "Sunset gradient");
    layer.putObject(c("Type"), s("gradientLayer"), fill);

    var ref = new ActionReference();
    ref.putClass(s("contentLayer"));
    var desc = new ActionDescriptor();
    desc.putReference(c("null"), ref);
    desc.putObject(c("Usng"), s("contentLayer"), layer);
    executeAction(c("Mk  "), desc, DialogModes.NO);
}

function makePoster() {
    var W = 1920, H = 1080;
    var oldRuler = app.preferences.rulerUnits;
    var oldType = app.preferences.typeUnits;
    app.preferences.rulerUnits = Units.PIXELS;
    app.preferences.typeUnits = TypeUnits.PIXELS;
    try {
        var doc = app.documents.add(W, H, 72, "Sunset Poster", NewDocumentMode.RGB);
        addSunsetGradient();

        var white = new SolidColor();
        white.rgb.red = 255; white.rgb.green = 255; white.rgb.blue = 255;

        var layer = doc.artLayers.add();
        layer.kind = LayerKind.TEXT;
        layer.name = "Name";
        var text = layer.textItem;
        text.contents = "FAYTH ELISA NAVARRO";
        text.font = "Arial-BoldMT";
        text.size = 100;
        text.color = white;
        text.justification = Justification.CENTER;
        text.position = [W / 2, H / 2];

        // Scale the name to fill 86% of the poster width, then centre it.
        var b = layer.bounds;
        var scale = (W * 0.86) / (b[2].value - b[0].value) * 100;
        layer.resize(scale, scale, AnchorPosition.MIDDLECENTER);
        b = layer.bounds;
        layer.translate(W / 2 - (b[0].value + b[2].value) / 2,
                        H / 2 - (b[1].value + b[3].value) / 2);

        b = layer.bounds;
        return "Made '" + doc.name + "' " + doc.width.value + "x" + doc.height.value +
               ", layers: " + doc.layers.length + ", font: " + layer.textItem.font +
               ", text spans x " + Math.round(b[0].value) + "-" + Math.round(b[2].value) +
               ", y " + Math.round(b[1].value) + "-" + Math.round(b[3].value);
    } finally {
        app.preferences.rulerUnits = oldRuler;
        app.preferences.typeUnits = oldType;
    }
}

makePoster();
