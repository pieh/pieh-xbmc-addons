# How to use script.rssclient (data provider for skinners)

or - how to attach rss feeds to my Home (or any other) window

## How to start addon

Basic run code:

	$<onfocus>XBMC.RunScript(script.rssclient,feed=FEED_URL,limit=15)</onfocus>
	
Full run code:

	$<onfocus>XBMC.RunScript(script.rssclient,feed=FEED_URL,imagecaching=TRUE|FALSE,htmlimg=TRUE|FALSE,limit=15,prefix=PREFIX)</onfocus>
	
Params:
1. feed - url to RSS feed
2. imagecaching - if set to true script will download images to userdata/Thumbnails/RSS directory. This enables usage of slideshow and multiimage control.
3. htmlimg - if enabled script will extract images from HTML image tags
4. limit - how much items to fetch
5. prefix - this is useful if You want to provide multiple feeds to multiple containers (lists) - it allows to distinguish between items from different feeds by adding prefix to them

## How to use data

Firstly let's understand how this script passes data to skin. Similiar to RecentlyAdded addon it sets window's properties. Properties name are formated:

	$RSS.x.Property
	
or (if prefix was specified):

	$PREFIX.RSS.x.Property
	
where x is number of RSS item

Properties are:
1. Title (RSS.1.Title) - title of the item
2. Desc (RSS.1.Desc) - description (text) of the item
3. Date (RSS.1.Date) - publish date of item
4. Channel (RSS.1.Channel) - name of channel where item was get from
5. Image (RSS.1.Image) - url of image attached to item (if no image was attached it will be empty)
6. Media (RSS.1.Media) - url of video attached to item (if no video was attached it will be empty)
7. ImageCount (RSS.1.ImageCount) - count of images attached to item
8. Image.X (RSS.1.Image.1) - url of Xth image attached to item (range from 1 to ImageCount, including ImageCount)
9. SlideShowable (RSS.1.SlideShowable) - if set to true it means we can use MultiImage control or builtin Slideshow function (ImageCaching must be enabled and item must have at least 2 images)
10. MultiImagePath (RSS.1.MultiImagePath) - path to directory containing images attached to item (usege in MultiImage control or Slideshow builtin), this property is set only of SlideShowable is set to true