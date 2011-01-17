# How to use script.rssclient (data provider for skinners)

or - how to attach rss feeds to my Home (or any other) window

## How to start addon

Basic run code:

	<onfocus>XBMC.RunScript(script.rssclient,feed=FEED_URL,limit=15)</onfocus>
	
Full run code:

	<onfocus>XBMC.RunScript(script.rssclient,feed=FEED_URL,imagecaching=TRUE|FALSE,htmlimg=TRUE|FALSE,limit=15,prefix=PREFIX)</onfocus>
	
**Params**:

	feed - url to RSS feed
	imagecaching - if set to true script will download images to userdata/Thumbnails/RSS directory. This enables usage of slideshow and multiimage control.
	htmlimg - if enabled script will extract images from HTML image tags
	limit - how much items to fetch
	prefix - this is useful if You want to provide multiple feeds to multiple containers (lists) - it allows to distinguish between items from different feeds by adding prefix to them

## How to use data

Firstly let's understand how this script passes data to skin. Similiar to RecentlyAdded addon it sets window's properties. Properties name are formated:

	RSS.x.Property
	
or (if prefix was specified):

	PREFIX.RSS.x.Property
	
where x is number of RSS item

**Properties**:

	Title (RSS.1.Title) - title of the item
	Desc (RSS.1.Desc) - description (text) of the item
	Date (RSS.1.Date) - publish date of item
	Channel (RSS.1.Channel) - name of channel where item was get from
	Image (RSS.1.Image) - url of image attached to item (if no image was attached it will be empty)
	Media (RSS.1.Media) - url of video attached to item (if no video was attached it will be empty)
	ImageCount (RSS.1.ImageCount) - count of images attached to item
	Image.X (RSS.1.Image.1) - url of Xth image attached to item (range from 1 to ImageCount, including ImageCount)
	SlideShowable (RSS.1.SlideShowable) - if set to true it means we can use MultiImage control or builtin Slideshow function (ImageCaching must be enabled and item must have at least 2 images)
	MultiImagePath (RSS.1.MultiImagePath) - path to directory containing images attached to item (usege in MultiImage control or Slideshow builtin), this property is set only of SlideShowable is set to true

There is also one more global property:

	RSS.count - holds count of RSS items passed to skin (usefull if script will return less items than skinner wanted - limit parameter)
	
**Using properites**:

1. Self written onclick (or onfocus) actions (fast, only properties that skinner will use will be set)

	
		<control type="list" id="XXX">
			[...] <- list parameters, etc.
			<content>
				<item id="1">
					<label>$INFO[Window.Property(RSS.1.Title)]</label>
					<label2>$INFO[Window.Property(RSS.1.Desc)]</label2>
					<onclick>SetProperty(RSS.Date,&quot;$INFO[Window.Property(RSS.1.Date)]&quot;)</onclick>
					<onclick>SetProperty(RSS.Channel,&quot;$INFO[Window.Property(RSS.1.Channel)]&quot;)</onclick>
					<onclick>SetProperty(RSS.Media,&quot;$INFO[Window.Property(RSS.1.Media)]&quot;)</onclick>
					<onclick>SetProperty(RSS.SlideShowable,&quot;$INFO[Window.Property(RSS.1.SlideShowable)]&quot;)</onclick>
					<onclick>SetProperty(RSS.MultiImagePath,&quot;$INFO[Window.Property(RSS.1.MultiImagePath)]&quot;)</onclick>
					<onclick>Control.SetFocus(30002)</onclick>
					<icon>$INFO[Window.Property(RSS.1.Image)]</icon>
					<thumb>-</thumb>
					<visible>IntegerGreaterThan(Window.Property(RSS.count),1)</visible>
				</item>
				[...] - rest of items
			</content>
		</control>

2. Using SettingScript to do the job (slower, as XBMC must find it, load it and finally execute it) - good 

		<control type="list" id="XXX">
			[...] <- list parameters, etc.
			<content>
				<item id="1">
					<label>$INFO[Window.Property(RSS.1.Title)]</label>
					<label2>$INFO[Window.Property(RSS.1.Desc)]</label2>
					<onclick>XBMC.RunScript($INFO[Window.Property(SettingScript)],id=1)</onclick>
					<onclick>Control.SetFocus(30002)</onclick>
					<icon>$INFO[Window.Property(RSS.1.Image)]</icon>
					<thumb>-</thumb>
					<visible>IntegerGreaterThan(Window.Property(RSS.count),1)</visible>
				</item>
				[...] - rest of items
			</content>
		</control>
	
To display item's I've used Group Control (Explanation of <onclick>Control.SetFocus(30002)</onclick>):

	<control type="group">
		[...] - controls displaying item's content, date, channel, header, image etc
		<control type="button" id="30002">
			<onup>XXX</onup>
			<ondown>XXX</ondown>
			<onleft>30004</onleft>
			<onright>30005</onright>
			<onclick>Control.SetFocus(XXX)</onclick>
			<posx>-20</posx>
			<posy>-20</posy>
			<width>1</width>
			<height>1</height>
			<visible>True</visible>
		</control>
		<control type="button" id="30004">
			<onfocus>SetFocus(30002)</onfocus>
			<onfocus>XBMC.PlayMedia($INFO[Window.Property(RSS.Media)])</onfocus>
			<posx>-20</posx>
			<posy>-20</posy>
			<width>1</width>
			<height>1</height>
			<visible>!StringCompare(Window.Property(RSS.Media),)</visible>
		</control>
		<control type="button" id="30004">
			<onfocus>SetFocus(30002)</onfocus>
			<posx>-20</posx>
			<posy>-20</posy>
			<width>1</width>
			<height>1</height>
			<visible>StringCompare(Window.Property(RSS.Media),)</visible>
		</control>
		<control type="button" id="30005">
			<onfocus>SetFocus(30002)</onfocus>
			<onfocus>XBMC.SlideShow($INFO[Window.Property(RSS.MultiImagePath)])</onfocus>
			<posx>-20</posx>
			<posy>-20</posy>
			<width>1</width>
			<height>1</height>
			<visible>Window.Property(RSS.SlideShowable)</visible>
		</control>
		<control type="button" id="30005">
			<onfocus>SetFocus(30002)</onfocus>
			<posx>-20</posx>
			<posy>-20</posy>
			<width>1</width>
			<height>1</height>
			<visible>!Window.Property(RSS.SlideShowable)</visible>
		</control>
		<visible>Control.HasFocus(30002)</visible>
	</control>
	
This skeleton code allow to display item's details and play attached media / show images slideshow. Now lets show user some item details - let's create more controls (labels, textboxes, images) to above Group Control:

	<label>$INFO[Container(XXX).ListItem(0).Label] - displaying current's item header</label>
	<label>$INFO[Container(XXX).ListItem(0).Label2] - displaying current's item text</label>
	<label>$INFO[Container(XXX).ListItem.Icon] - current's item image url (empty if there is no image)</label>
	<label>$INFO[Window.Property(RSS.Date)]</label>
	<label>$INFO[Window.Property(RSS.Channel)]</label>
	<visible>Window.Property(RSS.SlideShowable)</visible>
	<imagepath>$INFO[Window.Property(RSS.MultiImagePath)]</imagepath>
	<visible>StringCompare(Window.Property(RSS.ImageCount),1)</visible>
	
<visible>!StringCompare(Container(XXX).ListItem.Icon,)</visible> - checking if there is image for current item (control is visible if there is image)

	

	

	