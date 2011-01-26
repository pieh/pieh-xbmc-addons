# How to use script.rssclient (data provider for skinners)

or - how to attach rss feeds to my Home (or any other) window

## How to start addon

Basic run code:

	<onfocus>XBMC.RunScript(script.rssclient,feed=FEED_URL,limit=15)</onfocus>
	
Full run code:

	<onfocus>XBMC.RunScript(script.rssclient,feed=FEED_URL,feed=FEED_URL2,imagecaching=TRUE|FALSE,htmlimg=TRUE|FALSE,limit=15,prefix=PREFIX)</onfocus>
	
**Params**:

	feed - url to RSS feed (can be more than one)
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

First we have to populate some container control

	<control type="list" id="XXX">
		[...] <- list parameters, etc.
		<content>
			<item id="1">
				<label>$INFO[Window.Property(RSS.1.Title)]</label>
				<label2>$INFO[Window.Property(RSS.1.Desc)]</label2>
				<property name="RSS.Date">$INFO[Window.Property(RSS.1.Date)]</property>
				<property name="RSS.Channel">$INFO[Window.Property(RSS.1.Channel)]</property>
				<property name="RSS.Media">$INFO[Window.Property(RSS.1.Media)]</property>
				<property name="RSS.SlideShowable">$INFO[Window.Property(RSS.1.SlideShowable)]</property>
				<property name="RSS.MultiImagePath">$INFO[Window.Property(RSS.1.MultiImagePath)]</property>
				<property name="RSS.ImageCount">$INFO[Window.Property(RSS.1.ImageCount)]</property>
				<property name="RSS.Date">$INFO[Window.Property(RSS.1.Date)]</property>
				<icon>$INFO[Window.Property(RSS.1.Image)]</icon>
				<thumb>-</thumb>
				<visible>IntegerGreaterThan(Window.Property(RSS.count),1)</visible>
			</item>
			[...] - rest of items
		</content>
	</control>

To display items:

	<label>$INFO[Container(XXX).ListItem.Label]</label> - displaying current item header
	<label>$INFO[Container(XXX).ListItem.Label2]</label> - displaying current item text
	<label>$INFO[Container(XXX).ListItem.Icon]</label> - current item image url (empty if there is no image)
	<label>$INFO[Container(XXX).ListItem.Property(RSS.Date)]</label> - current item date
	<label>$INFO[Container(XXX).ListItem.Property(RSS.Channel)]</label> - current item channel
	<visible>Container(XXX).ListItem.Property(RSS.SlideShowable)</visible> - check if we can use MultiImage control or Slideshow 
	<imagepath>$INFO[Container(XXX).ListItem.Property(RSS.MultiImagePath)]</imagepath> - path for MultiImage control or Slideshow
	<visible>StringCompare(Container(XXX).ListItem.Icon,)</visible> - check if there is any image attached to item

Let's display indicator for user that video and slideshow feature is available for the item: (instruct to user to press Left/Right (to focus dummy button that will play the file on focus - <onleft>30004</onleft>/<onright>30005</onright>) 

	<control type="label">
		[...] - posx, posy, etc
		<label>Video is available</label>
		<visible>!StringCompare(Container(XXX).ListItem.Property(RSS.Media),)</visible>
	</control>

	<control type="label">
		[...] - posx, posy, etc
		<label>Slideshow is available</label>
		<visible>!StringCompare(Container(XXX).ListItem.Property(RSS.SlideShowable),)</visible>
	</control>
	