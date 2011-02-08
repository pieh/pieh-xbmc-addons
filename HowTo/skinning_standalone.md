# Skinning window for standalone RSS client

First of all name Your file 'script-rssclient-standalone-main.xml'.

## Important controls:

Container for RSS channels (List / wraplist / fixedlist / panel)
You need to add this (even if it will be just dummy control)

	<control type="list" id="30051">
		<description>Container for RSS channels</description>
		[ ... ]
	</control>
	
Container for RSS items (List / wraplist / fixedlist / panel)
You need to add this

	<control type="list" id="30050">
		<description>Container for RSS items</description>
		[ ... ]
	</control>
	
## Available info (for item list - container with id = 30050):
	
	ListItem.Label - Header of RSS item
	ListItem.Property(desc) - Text message of RSS item
	ListItem.Property(channeltext) - Name of channel to which RSS item belongs
	ListItem.Property(link) - Unique index of RSS item (often link to article)
	ListItem.Property(date) - Date of RSS item
	ListItem.Property(image) - Link to image attached to RSS item (empty if no image)
	ListItem.Property(imageCount) - Number of images attached to RSS item
	ListItem.Property(image.X) - Link to Xth image attached to RSS item (X is 1 to imageCount)
	ListItem.Property(slideshowable) - Returns 'true' if You can start slideshow/use multiimage control (there have to be more than 1 image and user have to enable image caching in addon settings)
	ListItem.Property(video) - Link to video attached to RSS item (empty if no video) 
	ListItem.Property(read) - Returns 'true' if user already read this item (if User press Select (Enter key in default keymap) or if User have item selected for more than 1.5 seconds)
	
## Some Examples:

Images - multiimage or image control. Group will be visible if there is any image (in particular first item)

	<control type="group">
		<control type="image">
			<posx>X</posx>
			<posy>Y</posy>
			<width>W</width>
			<height>H</height>
			<texture>$INFO[Container(30050).ListItem(0).Property(image)]</texture>
			<aspectratio scalediffuse="false" align="center" aligny="top">keep</aspectratio>
			<visible>!Container(30050).ListItem.Property(slideshowable)</visible>
		</control>	
		<control type="multiimage">
			<posx>X</posx>
			<posy>Y</posy>
			<width>W</width>
			<height>H</height>
			<imagepath>$INFO[Container(30050).ListItem(0).Property(multiimagepath)]</imagepath>
			<aspectratio scalediffuse="false" align="center" aligny="top">keep</aspectratio>
			<timeperimage>A</timeperimage>
			<fadetime>B</fadetime>
			<pauseatend>C</pauseatend>
			<randomize>D</randomize>
			<loop>E</loop>
			<visible>Container(30050).ListItem.Property(slideshowable)</visible>
		</control>
		<visible>!StringCompare(Container(30050).ListItem(0).Property(image),)</visible>
	</control>	
	
	