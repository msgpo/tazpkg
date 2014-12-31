#!/bin/sh
#
# TazPkg CGI interface - Manage packages via a browser
#
# This CGI interface extensively uses tazpkg to manage packages and have
# its own code for some tasks. Please KISS, it is important and keep speed
# in mind. Thanks, Pankso.
#
# (C) 2011-2014 SliTaz GNU/Linux - BSD License
#

. /lib/libtaz.sh
. lib/libtazpanel

. /etc/slitaz/slitaz.conf
. /etc/slitaz/tazpkg.conf

get_config
header


# xHTML 5 header with special side bar for categories.
TITLE=$(TEXTDOMAIN='tazpkg'; _ 'TazPanel - Packages')
xhtml_header | sed 's/id="content"/id="content-sidebar"/'

export TEXTDOMAIN='tazpkg'

pkg_info_link()
{
	echo "<a class=\"$2\" href=\"?info=${1//+/%2B}\">$1</a>" | sed 's| class=""||'
}


# Display localized short description

i18n_desc() {
	for L in $LANG ${LANG%%_*}; do
		if [ -e "$PKGS_DB/packages-desc.$L" ]; then
			LOCDESC=$(awk -F$'\t' -vp=$1 '{if ($1 == p) print $2}' $PKGS_DB/packages-desc.$L)
			if [ -n "$LOCDESC" ]; then
				SHORT_DESC="$LOCDESC"
				break
			fi
		fi
	done
}


# We need packages information for list and search

parse_packages_desc() {
	IFS="|"
	cut -f 1,2,3,5 -d "|" | while read PACKAGE VERSION SHORT_DESC WEB_SITE
	do
		class=pkg; [ -d $INSTALLED/${PACKAGE% } ] && class=pkgi
		i18n_desc $PACKAGE
		cat << EOT
<tr>
<td><input type="checkbox" name="pkg" value="$PACKAGE">$(pkg_info_link $PACKAGE $class)</td>
<td>$VERSION</td>
<td>$SHORT_DESC</td>
<td><a class="w" href="$WEB_SITE"></a></td>
</tr>
EOT
	done
	unset IFS
}


parse_packages_info() {
	IFS=$'\t'
	while read PACKAGE VERSION CATEGORY SHORT_DESC WEB_SITE TAGS SIZES DEPENDS; do
		class=pkg; grep -q "^$PACKAGE$'\t'" $PKGS_DB/installed.info && class=pkgi
		i18n_desc $PACKAGE
		cat << EOT
<tr>
<td><input type="checkbox" name="pkg" value="$PACKAGE">$(pkg_info_link $PACKAGE $class)</td>
<td>$VERSION</td>
<td>$SHORT_DESC</td>
<td><a class="w" href="$WEB_SITE"></a></td>
</tr>
EOT
	done
	unset IFS
}


# Parse mirrors list to be able to have an icon and remove link

list_mirrors() {
	while read line
	do
		cat << EOT
<li>
	<a href="?admin=rm-mirror=$line&amp;file=$(httpd -e $1)">
		<img src="$IMAGES/clear.png" title="$(_ 'Delete')" />
	</a>
	<a href="?admin=select-mirror&amp;mirror=$line">
		<img src="$IMAGES/start.png" title="$(_ 'Use as default')" />
	</a>
	<a href="$line">$line</a>
</li>
EOT
	done < $1
}


# Parse repositories list to be able to have an icon and remove link

list_repos() {
	ls $PKGS_DB/undigest 2> /dev/null | while read repo ; do
		cat <<EOT
	<li><a href="?admin=rm-repo=$repo">
		<img src="$IMAGES/clear.png">$repo</a></li>
EOT
	done
}


# Show button
show_button() {
	case $1 in
		recharge)     img='recharge'; label="$(_ 'Recharge list')" ;;
		up)           img='update';   label="$(_ 'Check upgrades')" ;;
		list)         img='tazpkg';   label="$(_ 'My packages')" ;;
		tag=)         img='';         label="$(_ 'Tags')" ;;
		linkable)     img='tazpkg';   label="$(_ 'Linkable packages')" ;;
		admin)        img='edit';     label="$(_ 'Administration')" ;;
		*Install*nf*) img='';         label="$(_ 'Install (Non Free)')" ;;
		*Install*)    img='';         label="$(_ 'Install')" ;;
		*Remove*)     img='stop';     label="$(_ 'Remove')" ;;
		*Block*)      img='';         label="$(_ 'Block')" ;;
		*Unblock*)    img='';         label="$(_ 'Unblock')" ;;
		*Repack*)     img='';         label="$(_ 'Repack')" ;;
		*saveconf*)   img='tazpkg';   label="$(_ 'Save configuration')" ;;
		*listconf*)   img='edit';     label="$(_ 'List configuration files')" ;;
		*quickcheck*) img='recharge'; label="$(_ 'Quick check')" ;;
		*fullcheck*)  img='recharge'; label="$(_ 'Full check')" ;;
	esac
	echo -n "<a class=\"button\" href=\"?$1\">"
	[ -n "$img" ] && echo -n "<img src=\"$IMAGES/$img.png\" />"
	echo "$label</a>"
}



#
# xHTML functions
#


# ENTER will search but user may search for a button, so put one.

search_form() {
	[ -z "$repo" ] && repo="$(GET repo)"
	[ -z "$repo" ] && repo="Any"
	cat << EOT
<div class="search">
	<form method="get" action="">
		<p>
			<input type="text" name="search" size="20">
			<input type="submit" value="$(gettext 'Search')">
			<input class="radius" type="submit" name="files" value="$(_n 'Files')">
		</p>
	</form>
</div>
EOT
}


table_head() {
	cat << EOT
<table class="zebra outbox pkglist">
	<thead>
		<tr>
			<td>$(_ 'Name')</td>
			<td>$(_ 'Version')</td>
			<td>$(_ 'Description')</td>
			<td>$(_ 'Web')</td>
		</tr>
	</thead>
	<tbody>
EOT
}


sidebar() {
	[ -z "$repo" ] && repo='Public'
	my=$(GET my); cat=$(GET cat)
	row='<tr><td><input type="submit" name="cat" value="'

	cat << EOT
<form method="get" action="">

<div id="sidebar">
	<select name="my" value="$my">
		<option value="my" $([ "$my" ] && echo -n "selected")>$(_ 'My packages')</option>
		<option value="" $([ ! "$my" ] && echo -n "selected")>$(_ 'All packages')</option>
	</select>

	<h4>$(_ 'Categories')</h4>

	<table class="side">
${row}base-system"  id="cat1"/><label for="cat1" class="a_base-system" >$(_ 'base-system')</label></td></tr>
${row}x-window"     id="cat2"/><label for="cat2" class="a_x-window"    >$(_ 'x-window')</label></td></tr>
${row}utilities"    id="cat3"/><label for="cat3" class="a_utilities"   >$(_ 'utilities')</label></td></tr>
${row}network"      id="cat4"/><label for="cat4" class="a_network"     >$(_ 'network')</label></td></tr>
${row}games"        id="cat5"/><label for="cat5" class="a_games"       >$(_ 'games')</label></td></tr>
${row}graphics"     id="cat6"/><label for="cat6" class="a_graphics"    >$(_ 'graphics')</label></td></tr>
${row}office"       id="cat7"/><label for="cat7" class="a_office"      >$(_ 'office')</label></td></tr>
${row}multimedia"   id="cat8"/><label for="cat8" class="a_multimedia"  >$(_ 'multimedia')</label></td></tr>
${row}development"  id="cat9"/><label for="cat9" class="a_development" >$(_ 'development')</label></td></tr>
${row}system-tools" id="cata"/><label for="cata" class="a_system-tools">$(_ 'system-tools')</label></td></tr>
${row}security"     id="catb"/><label for="catb" class="a_security"    >$(_ 'security')</label></td></tr>
${row}misc"         id="catc"/><label for="catc" class="a_misc"        >$(_ 'misc')</label></td></tr>
${row}meta"         id="catd"/><label for="catd" class="a_meta"        >$(_ 'meta')</label></td></tr>
${row}non-free"     id="cate"/><label for="cate" class="a_non-free"    >$(_ 'non-free')</label></td></tr>
${row}all"          id="catf"/><label for="catf" class="a_all"         >$(_ 'all')</label></td></tr>
${row}extra"        id="catg"/><label for="catg" class="a_extra"       >$(_ 'extra')</label></td></tr>
	</table>
EOT

	if [ -d $PKGS_DB/undigest ]; then
		cat << EOT
	<h4>$(_ 'Repository')</h4>

	<select name="repo" value="$repo">
		<option value="Public" $([ "$repo" == "Public" ] && echo -n "selected")>$(_ 'Public')</option>
		$(for i in $(ls $PKGS_DB/undigest); do
			echo -n "<option value=\"$i\""
			[ "$repo" == "$i" ] && echo -n " selected"
			echo ">$i</option>"
		done)
		<option value="Any" $([ "$repo" == "Any" ] && echo -n "selected")>$(_ 'Any')</option>
	</select>

	<input type="submit" name="tag" value="" id="tags"><label for="tags">$(_ 'All tags...')</label>
	<input type="submit" name="cat" value="" id="cats"><label for="cats">$(_ 'All categories...')</label>
EOT
	fi
	echo "</div>"
}


repo_list() {
	if [ -n "$(ls $PKGS_DB/undigest/ 2> /dev/null)" ]; then
		case "$repo" in
			Public)
				;;
			""|Any)
				for i in $PKGS_DB/undigest/* ; do
					[ -d "$i" ] && echo "$i$1"
				done ;;
			*)
				echo "$PKGS_DB/undigest/$repo$1"
				return ;;
		esac
	fi
	echo "$PKGS_DB$1"
}


repo_name() {
	case "$1" in
		$PKGS_DB)
			echo "Public" ;;
		$PKGS_DB/undigest/*)
			echo ${1#$PKGS_DB/undigest/} ;;
	esac
}


# Print links to the pages

pager() {
	awk -F'"' -vpage="$page" -vnum_lines="$(wc -l < $1)" -vtext="$(_ 'Pages:') " -vurl="?cat=$category&amp;repo=$repo&amp;page=" '
BEGIN{
	num_pages = int(num_lines / 100) + (num_lines % 100 != 0)
	if (num_pages != 1) printf "<p>%s", text
}
{
	if (num_pages == 1) exit
	r = NR % 100
	if (r == 1) {
		p = int(NR / 100) + 1
		printf "<a class=\"pages%s\" href=\"%s%s\" title=\"%s\n···\n", p==page?" current":"", url, p, $6
	} else if (r == 0)
		printf "%s\">%s</a> ", $6, int(NR / 100)
}
END{
	if (num_pages == 1) exit
	if (r != 0) printf "%s\">%s</a>", $6, int(NR / 100) + 1
	print "</p>"
}' $1
}


# Show packages list by category or tag

show_list() {
	cached=$(mktemp)
	{
		for L in $LANG ${LANG%%_*}; do
			if [ -e "$PKGS_DB/packages-desc.$L" ]; then
				sed '/^#/d' $PKGS_DB/packages-desc.$L; break
			fi
		done
		[ -e "$i/blocked-packages.list" ] && cat $i/blocked-packages.list
		sed 's|.*|&\ti|' $i/installed.info
		[ "$category" == 'extra' ] || [ $1 == 'my' ] || cat $i/packages.info
		[ "$category" == 'extra' ] && sed 's|.*|&\t-\textra\t-\thttp://mirror.slitaz.org/packages/get/&\t-\t-\t-|' $PKGS_DB/extra.list
	} | sort -t$'\t' -k1,1 | sed '/^$/d' | awk -F$'\t' -vc="${category:--}" -vt="${tag:--}" '
{
	if (PKG && PKG != $1) {
		if (SEL) {
			if (DSCL) DSC = DSCL
			printf "<tr><td><input type=\"checkbox\" name=\"pkg\" value=\"%s\"><a class=\"pkg%s%s\" href=\"?info=%s\">%s</a></td><td>%s</td><td>%s</td><td><a href=\"%s\"></a></td></tr>\n", PKG, INS, BLK, gensub(/\+/, "%2B", "g", PKG), PKG, VER, DSC, WEB
		}
		VER = DSC = WEB = DSCL = INS = BLK = SEL = ""
	}

	PKG = $1
	if (NF == 1) { BLK = "b"; next }
	if (NF == 2) { DSCL = $2; next }
	if (c == "all" || $3 == c || index(" "$6" ", " "t" ")) { SEL = 1 }
	if (SEL) {
		if ($9 == "i") { VER = $2; DSC = $4; WEB = $5; INS = "i"; next}
		if (! INS)     { VER = $2; DSC = $4; WEB = $5 }
	}
}' > $cached
	page=$(GET page); [ -z "$page" ] && page=1

	pager="$(pager $cached)"
	if [ "$pager" != "<p>$(_ 'Pages:') </p>" ]; then
		[ "$repo" != "Public" ] && echo "<h3>$(_ 'Repository: %s' $(repo_name $i))</h3>"
		echo "$pager"

		table_head
		tail -n+$((($page-1)*100+1)) $cached | head -n100
		echo "</tbody></table>"

		echo "$pager"
	fi
	rm -f $cached
}


# Show links for "info" page

show_info_links() {
	if [ -n "$1" ]; then
		echo -n "<tr><td><b>$2</b></td><td>"
		echo $1 | tr ' ' $'\n' | awk -vt="$3" '{
			printf "<a href=\"?%s=%s\">%s</a> ", t, gensub(/\+/, "%2B", "g", $1), $1
		}'
		echo "</td></tr>"
	fi
}



#
# Commands
#


case " $(GET) " in
	*\ linkable\ *)
		#
		# List linkable packages.
		#
		search_form
		sidebar
		LOADING_MSG=$(_ 'Listing linkable packages...')
		loading_msg
		cat << EOT
<h2>$(_ 'Linkable packages')</h2>

<input type="hidden" name="do" value="Link" />
<div id="actions">
	<div class="float-left">
		$(_ 'Selection:')
		<input type="submit" value="$(_ 'Link')" />
	</div>
	<div class="float-right">
		$(show_button recharge)
		$(show_button up)
	</div>
</div>
EOT
		table_head
		target=$(readlink $PKGS_DB/fslink)
		for pkg in $(ls $target/$INSTALLED); do
			[ -s $pkg/receipt ] && continue
			. $target/$INSTALLED/$pkg/receipt
			i18n_desc $pkg
			cat << EOT
<tr>
	<td><input type="checkbox" name="pkg" value="$pkg" /><a class="pkg" href="?info=${pkg//+/%2B}">$pkg</a></td>
	<td>$VERSION</td>
	<td>$SHORT_DESC</td>
	<td><a class="w" href="$WEB_SITE"></a></td>
</tr>
EOT
		done
		cat << EOT
		</tbody>
	</table>
</form>
EOT
		;;


	*\ cat\ *)
		#
		# List all packages by category.
		#
		my=$(GET my); category=$(GET cat); repo=$(GET repo)
		search_form
		sidebar | sed "s/a_$category/active/;s/repo_$repo/active/"
		if [ -z "$category" ] || [ "$category" == 'cat' ]; then
			cat << EOT
<h2>$(_ 'Categories list')</h2>

<table class="zebra outbox">
	<thead>
		<tr>
			<td>$(_ 'Category')</td>
			<td>$(_ 'Repository')</td>
			<td>$(_ 'Installed')</td>
		</tr>
	</thead>
	<tbody>
EOT
			params="&amp;my=$my&amp;repo=$repo" # don't forget it unexpectedly
			{
				awk -F$'\t' '{print $3}' $PKGS_DB/packages.info | sort | uniq -c
				awk -F$'\t' '{print $3}' $PKGS_DB/installed.info | sed 's|.*|& i|' | sort | uniq -c
			} | sort -k2,2 | awk '
			{
				c [$2] = "."
				if ($3) { i[$2] = $1; } else { m[$2] = $1; }
			}
			END {
				for (n in c) print n, m[n], i[n]
			}' | sort | awk -vp="$params" '{
			printf "<tr><td><a href=\"?cat=%s%s\">%s</a></td><td>%d</td><td>%d</td></tr>", $1, p, $1, $2, $3
			}'
			echo '</tbody></table>'
		else
			LOADING_MSG="$(_ 'Listing packages...')"
			loading_msg
			cat << EOT
<h2>$(_ 'Category: %s' $category)</h2>

<div id="actions">
	<div class="float-left">
		$(_ 'Selection:')
		<input type="submit" name="do" value="Install" />
		<input type="submit" name="do" value="Remove" />
	</div>
	<div class="float-right">
		$(show_button recharge)
		$(show_button up)
	</div>
</div>
EOT
			for i in $(repo_list ""); do
				show_list $my
			done
			echo '</form>'
		fi
		;;


	*\ search\ *)
		#
		# Search for packages. Here default is to search in packages.desc
		# and so get result including packages names and descriptions
		#
		pkg=$(GET search); [ -z "$pkg" ] && xhtml_footer && exit
		repo=$(GET repo)
		cd $PKGS_DB
		search_form
		sidebar | sed "s/repo_$repo/active/"
		LOADING_MSG="$(_ 'Searching packages...')"
		loading_msg
		cat << EOT
<h2>$(_ 'Search packages')</h2>

<div id="actions">
	<div class="float-left">
		$(_ 'Selection:')
		<input type="submit" name="do" value="Install" />
		<input type="submit" name="do" value="Remove" />
		<a href="$(cat $PANEL/lib/checkbox.js)">$(_ 'Toogle all')</a>
	</div>
	<div class="float-right">
		$(show_button recharge)
		$(show_button up)
	</div>
</div>
<input type="hidden" name="repo" value="$repo" />
EOT
		if [ -n "$(GET files)" ]; then
			cat <<EOT
	<table class="zebra outbox filelist">
	<thead>
		<tr>
			<td>$(_ 'Package')</td>
			<td>$(_ 'File')</td>
		</tr>
	<thead>
	<tbody>
EOT
			lzcat $(repo_list /files.list.lzma) | grep -Ei ": .*$(GET search)" | \
			while read PACKAGE FILE; do
				PACKAGE=${PACKAGE%:}
				class=pkg; [ -d $INSTALLED/$PACKAGE ] && class=pkgi
				cat << EOT
<tr>
	<td><input type="checkbox" name="pkg" value="$PACKAGE">$(pkg_info_link $PACKAGE $class)</td>
	<td>$(echo "$FILE" | sed "s|$pkg|<span class=\"diff-add\">$pkg</span>|g")</td>
</tr>
EOT
			done
		else
			table_head
			awk -F$'\t' 'BEGIN{IGNORECASE = 1}
			$1 $4 ~ /'$pkg'/{print $0}' $(repo_list /packages.info) | parse_packages_info
		fi
		cat << EOT
	</tbody>
	</table>
</form>
EOT
		;;


	*\ recharge\ *)
		#
		# Lets recharge the packages list
		#
		search_form
		sidebar
		LOADING_MSG="$(_ 'Recharging lists...')"
		loading_msg
		cat << EOT
<h2>$(_ 'Recharge')</h2>

<div id="actions">
	<div class="float-left">
		<p>$(_ 'Recharge checks for new or updated packages')</p>
	</div>
	<div class="float-right">
		$(show_button up)
	</div>
</div>
<div class="wrapper">
<pre>
EOT
		echo $(_ 'Recharging packages list') | log
		tazpkg recharge | filter_taztools_msgs
		cat << EOT
</pre>
</div>
<p>$(_ 'Packages lists are up-to-date. You should check for upgrades now.')</p>
EOT
		;;


	*\ up\ *)
		#
		# Upgrade packages
		#
		cd $PKGS_DB
		search_form
		sidebar
		LOADING_MSG="$(_ 'Checking for upgrades...')"
		loading_msg
		cat << EOT
<h2>$(_ 'Up packages')</h2>

<div id="actions">
	<div class="float-left">
		$(_ 'Selection:')
		<input type="submit" name="do" value="Install" />
		<input type="submit" name="do" value="Remove" />
		<a href="$(cat $PANEL/lib/checkbox.js)">$(_ 'Toogle all')</a>
	</div>
	<div class="float-right">
		$(show_button recharge)
	</div>
</div>
EOT
		tazpkg up --check >/dev/null
		table_head
		for pkg in $(cat packages.up); do
			grep -hs "^$pkg |" $PKGS_DB/packages.desc $PKGS_DB/undigest/*/packages.desc | \
				parse_packages_desc
		done
		cat << EOT
</tbody>
</table>
</form>
EOT
		;;


	*\ do\ *)
		#
		# Do an action on one or some packages
		#
		opt=""
		pkgs=""
		cmdline=$(echo ${QUERY_STRING#do=} | sed s'/&/ /g')
		cmd=$(echo ${cmdline} | awk '{print $1}')
		cmdline=${cmdline#*repo=* }
		pkgs=$(echo $cmdline | sed -e s'/+/ /g' -e s'/pkg=//g' -e s/$cmd//)
		pkgs="$(httpd -d "$pkgs")"
		cmd=$(echo $cmd | tr [:upper:] [:lower:])
		case $cmd in
			install)
				cmd=get-install opt=--forced
				LOADING_MSG="get-installing packages..."
				;;
			link)
				opt=$(readlink $PKGS_DB/fslink)
				LOADING_MSG="linking packages..."
				;;
		esac
		search_form
		sidebar
		loading_msg
		cat << EOT
<h2>TazPkg: $cmd</h2>

<div id="actions">
	<div class="float-left">
		<p>$(_ 'Performing tasks on packages')</p>
	</div>
</div>
<div class="box">
	$(_ 'Executing %s for: %s' $cmd $pkgs)
</div>
EOT
		for pkg in $pkgs; do
			echo '<pre>'
				echo $(_n 'y') | tazpkg $cmd $pkg $opt 2>/dev/null | filter_taztools_msgs
			echo '</pre>'
		done ;;


	*\ info\ *)
		#
		# Packages info
		#
		pkg=$(GET info)
		search_form
		sidebar
		if [ -d $INSTALLED/$pkg ]; then
			. $INSTALLED/$pkg/receipt
			files=$(wc -l < $INSTALLED/$pkg/files.list)
			action="Remove"
		else
			cd $PKGS_DB
			LOADING_MSG=$(_ 'Getting package info...')
			loading_msg
			eval "$(awk -F$'\t' -vp=$pkg '
			$1==p{
				printf "PACKAGE=\"%s\"; VERSION=\"%s\"; CATEGORY=\"%s\"; ", $1, $2, $3
				printf "SHORT_DESC=\"%s\"; WEB_SITE=\"%s\"; TAGS=\"%s\"; ", $4, $5, $6
				printf "SIZES=\"%s\"; DEPENDS=\"%s\"", $7, $8
			}' packages.info undigest/*/packages.info)"
			PACKED_SIZE=${SIZES% *}
			UNPACKED_SIZE=${SIZES#* }

			action="Install"
			temp="${pkg#get-}"
		fi
		cat << EOT
<h2>$(_ 'Package %s' $PACKAGE)</h2>

<div id="actions">
	<div class="float-left">
		<p>
EOT
		if [ "$temp" != "$pkg" -a "$action" == "Install" ]; then
			show_button "do=Install&amp;$temp&amp;nf"
		else
			show_button "do=$action&amp;$pkg"
		fi

		if [ -d $INSTALLED/$pkg ]; then
			if grep -qs "^$pkg$" $PKGS_DB/blocked-packages.list; then
				show_button "do=Unblock&amp;$pkg"
			else
				show_button "do=Block&amp;$pkg"
			fi
			show_button "do=Repack&amp;$pkg"
		fi
		i18n_desc $pkg
		cat << EOT
		</p>
	</div>
</div>
<table class="zebra outbox">
<tbody>
	<tr><td><b>$(_ 'Name')</b></td><td>$PACKAGE</td></tr>
	<tr><td><b>$(_ 'Version')</b></td><td>$VERSION</td></tr>
	<tr><td><b>$(_ 'Category')</b></td><td><a href="?cat=$CATEGORY">$CATEGORY</a></td></tr>
	<tr><td><b>$(_ 'Description')</b></td><td>$SHORT_DESC</td></tr>
	$([ -n "$MAINTAINER" ] && echo "<tr><td><b>$(_ 'Maintainer')</b></td><td>$MAINTAINER</td></tr>")
	$([ -n "$LICENSE" ] && echo "<tr><td><b>$(_ 'License')</b></td><td><a href=\"?license=$pkg\">$LICENSE</a></td></tr>")
	<tr><td><b>$(_ 'Website')</b></td><td><a href="$WEB_SITE">$WEB_SITE</a></td></tr>
	$(show_info_links "$TAGS" "$(_ 'Tags')" 'tag')
	<tr><td><b>$(_ 'Sizes')</b></td><td>$PACKED_SIZE/$UNPACKED_SIZE</td></tr>
	$(show_info_links "$DEPENDS" "$(_ 'Depends')" 'info')
	$(show_info_links "$SUGGESTED" "$(_ 'Suggested')" 'info')
</tbody>
</table>
EOT
		DESC="$(tazpkg desc $pkg)"
		[ -n "$DESC" ] && echo "<pre>$DESC</pre>"

		if [ -d $INSTALLED/$pkg ]; then
			cat << EOT
<p>$(_ 'Installed files: %s' $(wc -l < $INSTALLED/$pkg/files.list))</p>

<pre>$(sort $INSTALLED/$pkg/files.list)</pre>
EOT
		else
			cat << EOT
<p>$(_ 'Installed files: %s' ' ')</p>

<pre>
$(lzcat files.list.lzma undigest/*/files.list.lzma 2> /dev/null | awk -vp="$pkg:" '$1==p{print $2}' | sort)
</pre>
EOT
		fi
		;;


	*\ admin\ * )
		#
		# TazPkg configuration page
		#
		echo '</form>'
		cmd=$(GET admin)
		case "$cmd" in
			clean)
				rm -rf $CACHE_DIR/* ;;
			add-mirror)
				# Decode url
				mirror=$(GET mirror)
				case "$mirror" in
				http://*|ftp://*)
					echo "$mirror" >> $(GET file) ;;
				esac ;;
			rm-mirror=http://*|rm-mirror=ftp://*)
				mirror=${cmd#rm-mirror=}
				sed -i -e "s@$mirror@@" -e '/^$/d' $(GET file) ;;
			select-mirror*)
				release=$(cat /etc/slitaz-release)
				mirror="$(GET mirror)packages/$release/"
				tazpkg setup-mirror $mirror | log
				;;
			add-repo)
				# Decode url
				mirror=$(GET mirror)
				repository=$PKGS_DB/undigest/$(GET repository)
				case "$mirror" in
				http://*|ftp://*)
					mkdir -p $repository
					echo "$mirror" > $repository/mirror
					echo "$mirror" > $repository/mirrors ;;
				esac ;;
			rm-repo=*)
				repository=${cmd#rm-repo=}
				rm -rf $PKGS_DB/undigest/$repository ;;
		esac
		[ "$cmd" == "$(_n 'Set link')" ] &&
			[ -d "$(GET link)/$INSTALLED" ] && ln -fs $(GET link) $PKGS_DB/fslink
		[ "$cmd" == "$(_n 'Remove link')" ] && rm -f $PKGS_DB/fslink

		cache_files=$(find $CACHE_DIR -name *.tazpkg | wc -l)
		cache_size=$(du -sh $CACHE_DIR | cut -f1 | sed 's|\.0||')
		sidebar
		cat << EOT
<h2>$(_ 'Administration')</h2>
<div>
	<p>$(_ 'TazPkg administration and settings')</p>
</div>
<div id="actions">
	$(show_button 'admin=&amp;action=saveconf')
	$(show_button 'admin=&amp;action=listconf')
	$(show_button 'admin=&amp;action=quickcheck')
	$(show_button 'admin=&amp;action=fullcheck')
</div>
EOT
		case "$(GET action)" in
				saveconf)
					LOADING_MSG=$(_ 'Creating the package...')
					loading_msg
					echo "<pre>"
					cd $HOME
					tazpkg repack-config | filter_taztools_msgs
					echo -n "$(_ 'Path:') "; ls $HOME/config-*.tazpkg
					echo "</pre>" ;;
				listconf)
					echo "<h4>$(_ 'Configuration files')</h4>"
					echo "<ul>"
					tazpkg list-config | while read file; do
						if [ -e $file ]; then
							echo "<li><a href=\"index.cgi?file=$file\">$file</a></li>"
						else
							echo "<li>$file</li>"
						fi
					done
					echo "</ul>"
					;;
				quickcheck)
					LOADING_MSG=$(_ 'Checking packages consistency...')
					loading_msg
					echo "<pre>"
					tazpkg check
					echo "</pre>" ;;
				fullcheck)
					LOADING_MSG=$(_ 'Full packages check...')
					loading_msg
					echo "<pre>"
					tazpkg check --full
					echo "</pre>" ;;
				esac
		cat << EOT
<h3>$(_ 'Packages cache')</h3>

<div>
	<form method="get" action="">
		<p>$(_ 'Packages in the cache: %s (%s)' $cache_files $cache_size)
			<input type="hidden" name="admin" value="clean" />
			<input type="submit" value="$(_n 'Clean')" />
		</p>
	</form>
</div>

<h3>$(_ 'Default mirror')</h3>

<pre>$(cat $PKGS_DB/mirror)</pre>

<h3>$(_ 'Current mirror list')</h3>
EOT
		for i in $PKGS_DB/mirrors $PKGS_DB/undigest/*/mirrors; do
			[ -s $i ] || continue
			echo '<div class="box">'
			if [ $i != $PKGS_DB/mirrors ]; then
				Repo_Name="$(repo_name $(dirname $i))"
				echo "<h4>$(_ 'Repository: %s' $Repo_Name)</h4>"
			fi
			echo "<ul>"
			list_mirrors $i
			echo "</ul>"
			cat << EOT
</div>
<form method="get" action="">
	<p>
		<input type="hidden" name="admin" value="add-mirror" />
		<input type="hidden" name="file" value="$i" />
		<input type="text" name="mirror" size="60">
		<input type="submit" value="$(_n 'Add mirror')" />
	</p>
</form>
EOT
		done
		echo "<h3>$(_ 'Private repositories')</h3>"
		[ -n "$(ls $PKGS_DB/undigest 2> /dev/null)" ] && cat << EOT
<div class="box">
	<ul>
		$(list_repos)
	</ul>
</div>
EOT
		cat << EOT
<form method="get" action="">
	<p>
		<input type="hidden" name="admin" value="add-repo" />
		$(_ 'Name') <input type="text" name="repository" size="10">
		$(_ 'mirror')
		<input type="text" name="mirror" value="http://" size="50">
		<input type="submit" value="$(_n 'Add repository')" />
	</p>
</form>

<h3>$(_ 'Link to another SliTaz installation')</h3>

<p>$(_ "This link points to the root of another SliTaz installation. \
You will be able to install packages using soft links to it.")</p>

<form method="get" action="">
<p>
	<input type="text" name="link" value="$(readlink $PKGS_DB/fslink 2> /dev/null)" size="50">
	<input type="submit" name="admin" value="$(_ 'Set link')" />
	<input type="submit" name="admin" value="$(_ 'Remove link')" />
</p>
</form>
EOT
		version=$(cat /etc/slitaz-release)
		cat << EOT

<h3 id="dvd">$(_ 'SliTaz packages DVD')</h3>

<p>$(_ "A bootable DVD image of all available packages for the %s version is \
generated every day. It also contains a copy of the website and can be used \
without an internet connection. This image can be installed on a DVD or a USB \
key." $version)</p>

<div>
	<form method="post" action='?admin&amp;action=dvdimage#dvd'>
	<p>
		<a class="button"
			href='http://mirror.slitaz.org/iso/$version/packages-$version.iso'>
			<img src="$IMAGES/tazpkg.png" />$(_ 'Download DVD image')</a>
		<a class="button" href='?admin&amp;action=dvdusbkey#dvd'>
			<img src="$IMAGES/tazpkg.png" />$(_ 'Install from DVD/USB key')</a>
	</p>
	<div class="box">
		$(_ 'Install from ISO image:')
		<input type="text" name="dvdimage" size="40" value="/root/packages-$version.iso">
	</div>
	</form>
</div>
EOT
		if [ "$(GET action)" == "dvdimage" ]; then
			dev=$(POST dvdimage)
			mkdir -p /mnt/packages 2> /dev/null
			echo "<pre>"
			mount -t iso9660 -o loop,ro $dev /mnt/packages &&
			/mnt/packages/install.sh &&
			_ '%s is installed on /mnt/packages' $dev
			echo "</pre>"
		fi
		if [ "$(GET action)" == "dvdusbkey" ]; then
			mkdir -p /mnt/packages 2> /dev/null
			for tag in "LABEL=\"packages-$version\" TYPE=\"iso9660\"" \
				"LABEL=\"sources-$version\" TYPE=\"iso9660\"" ; do
				dev=$(blkid | grep "$tag" | cut -d: -f1)
				[ -n "$dev" ] || continue
				echo "<pre>"
				mount -t iso9660 -o ro $dev /mnt/packages &&
				/mnt/packages/install.sh &&
				_ '%s is installed on /mnt/packages' $dev
				echo "</pre>"
				break
			done
		fi
		;;


	*\ license\ *)
		#
		# Show licenses for installed packages
		#
		search_form
		sidebar
		pkg=$(GET license)
		case $pkg in
			/*)
				[ -e $pkg ] && {
				echo "<h2>${pkg#/usr/share/licenses/}</h2>"
				case $pkg in
					*.htm*)
						cat $pkg ;;
					*)
						echo "<pre style=\"white-space: pre-wrap\">"
						cat $pkg | htmlize | sed 's|\([hf]t*t*ps*://[a-zA-Z0-9./_-]*[a-zA-Z0-9/_-]\)|<a href="\1">\1</a>|'
						echo "</pre>"
						;;
				esac
				} ;;
			*)
				echo "<h2>$(_ 'Licenses for package %s' $pkg)</h2>"
				ONLINE=''; OFFLINE=''

				if [ -e "$PKGS_DB/installed/$pkg" ]; then
					for license in $(. $PKGS_DB/installed/$pkg/receipt; echo "$LICENSE"); do
						OSL=''; GNU=''; USR=''; LIC=''
						case $license in
							Apache)			OSL='Apache-2.0'; URL='http://www.apache.org/licenses/' ;;
							Artistic)		OSL='Artistic-2.0' ;;
							BSD)			OSL='BSD-2-Clause' ;;
							BSD3)			OSL='BSD-3-Clause' ;;

							CC-BY-SA*|CC-SA*)	CCO='by-sa/4.0/' ;;
							CC-BY-ND*)		CCO='by-nd/4.0/' ;;
							CC-BY-NC-SA*)	CCO='by-nc-sa/4.0/' ;;
							CC-BY-NC-ND*)	CCO='by-nc-nd/4.0/' ;;
							CC-BY-NC*)		CCO='by-nc/4.0/' ;;
							CC-BY*)			CCO='by/4.0/' ;;

							cc-pd)			URL='http://creativecommons.org/publicdomain/' ;;
							CCPL)			;;
							CDDL*)			OSL='CDDL-1.0' ;;
							CECILL*)		OSL='CECILL-2.1' ;;
							Eclipse|EPL*)	OSL='EPL-1.0' ;;
							FDL)			GNU='fdl' ;;
							GPL)			GNU='gpl'; OSL='gpl-license'; LIC='gpl.txt' ;;
							GPL2)			GNU='old-licenses/gpl-2.0'; OSL='GPL-2.0' ;;
							GPL3)			GNU='gpl'; OSL='GPL-3.0'; LIC='gpl.txt' ;;
							ISC)			OSL='ISC' ;;
							LGPL)			GNU='lgpl'; OSL='lgpl-license' ;;
							LGPL2)			GNU='old-licenses/lgpl-2.0' ;;
							LGPL2.1)		GNU='old-licenses/lgpl-2.1'; OSL='LGPL-2.1'; LIC='lgpl.txt' ;;
							LGPL3)			GNU='lgpl'; OSL='LGPL-3.0' ;;
							LPPL*)			OSL='LPPL-1.3c' ;;
							MIT)			OSL='MIT'; LIC='mit.txt' ;;
							MPL)			OSL='MPL-2.0'; LIC='mozilla.txt' ;;
							MPL2)			OSL='MPL-2.0' ;;
							FL)				OSL='Fair' ;; # ?
							PSL)			;;
							PublicDomain)	;;
							QPL*)			OSL='QPL-1.0' ;;
							SIL_OFL*)		OSL='OFL-1.1' ;;
							zlib/libpng)	OSL='Zlib' ;;
						esac

						[ -n "$OSL" ] && ONLINE="$ONLINE	<li><a href=\"http://opensource.org/licenses/$OSL\">$(_ '%s license on %s website' "<b>$OSL</b>" "OSL")</a></li>\n"
						[ -n "$GNU" ] && ONLINE="$ONLINE	<li><a href=\"https://www.gnu.org/licenses/$GNU.html\">$(_ '%s license on %s website' "<b>${GNU#*/}</b>" "GNU")</a></li>\n"
						[ -n "$CCO" ] && ONLINE="$ONLINE	<li><a href=\"http://creativecommons.org/licenses/$CCO\">$(_ '%s license on %s website' "<b>${CCO%%/*}</b>" "Creative Commons")</a></li>\n"
						[ -n "$URL" ] && ONLINE="$ONLINE	<li><a href=\"$URL\">$URL</a></li>\n"
						[ -n "$LIC" ] && OFFLINE="$OFFLINE	<li><a href=\"?license=/usr/share/licenses/$LIC\">licenses/<b>$LIC</b></a></li>\n"
					done

					for lic in $(grep /usr/share/licenses/ $PKGS_DB/installed/$pkg/files.list); do
						OFFLINE="$OFFLINE	<li><a href=\"?license=$lic\">licenses/<b>${lic#/usr/share/licenses/}</b></a></li>\n"
					done
				fi
				[ -n "$ONLINE" ] && echo -e "<p>$(_ 'Read online:')</p>\n<ul>\n$ONLINE</ul>\n"
				[ -n "$OFFLINE" ] && echo -e "<p>$(_ 'Read local:')</p>\n<ul>\n$OFFLINE</ul>\n"
				;;
		esac
		;;


	*\ tag\ *)
		#
		# Show packages with matching tag; show tag cloud
		#
		search_form
		sidebar
		tag=$(GET tag); repo=$(GET repo); my=$(GET my)
		[ -z "$repo" ] && repo='Any'
		if [ -n "$tag" ]; then
			cat << EOT
<h2>$(_ 'Tag "%s"' $tag)</h2>

<div id="actions">
	<div class="float-left">
		$(_ 'Selection:')
		<input type="submit" name="do" value="Install" />
		<input type="submit" name="do" value="Remove" />
	</div>
</div>
EOT
			for i in $(repo_list ""); do
				show_list all
			done
			echo '</form>'

		else
			params="&amp;my=$my&amp;repo=$repo" # don't forget it unexpectedly
			echo "<h2>$(_ 'Tags list')</h2>"
			echo "<p>"
			TAGS="$(awk -F$'\t' '{if($6){print $6}}' $PKGS_DB/packages.info | tr ' ' $'\n' | sort | uniq -c)"
			MAX="$(echo "$TAGS" | awk '{if ($1 > MAX) MAX = $1} END{print MAX}')"
			echo "$TAGS" | awk -vMAX="$MAX" -vp="$params" '{
				printf "<a class=\"tag%s\" href=\"?tag=%s%s\" title=\"%s\">%s</a> ", int($1 * 7 / MAX + 1), $2, p, $1, $2
			}'
			echo "</p>"
		fi
		;;


		*)
		#
		# Default to summary
		#
		search_form
		sidebar
		[ -n "$(GET block)" ] && tazpkg block $(GET block)
		[ -n "$(GET unblock)" ] && tazpkg unblock $(GET unblock)
		cat << EOT
<h2>$(_ 'Summary')</h2>

<div id="actions">
EOT
		fslink=$(readlink $PKGS_DB/fslink)
		[ -n "$fslink" -a -d "$fslink/$INSTALLED" ] && show_button linkable
		show_button recharge
		show_button up
		show_button admin
		cat << EOT
</div>

<table class="zebra outbox">
<tbody>
<tr><td>$(_ 'Last recharge:')</td><td>
EOT
		ls -l $PKGS_DB/packages.list | awk '{print $6, $7, $8}'
		if [ -n "$(find $PKGS_DB/packages.list -mtime +10)" ]; then
			_ '(Older than 10 days)'
		else
			_ '(Not older than 10 days)'
		fi
		cat << EOT
</td></tr>
<tr><td>$(_ 'Installed packages:')</td>
	<td>$(cat $PKGS_DB/installed.info | wc -l)</td></tr>
<tr><td>$(_ 'Mirrored packages:')</td>
	<td>$(cat $PKGS_DB/packages.list | wc -l)</td></tr>
<tr><td>$(_ 'Upgradeable packages:')</td>
	<td>$(cat $PKGS_DB/packages.up | wc -l)</td></tr>
<tr><td>$(_ 'Installed files:')</td>
	<td>$(cat $INSTALLED/*/files.list | wc -l)</td></tr>
<tr><td>$(_ 'Blocked packages:')</td>
	<td>$(cat $PKGS_DB/blocked-packages.list | wc -l)</td></tr>
</tbody>
</table>

<h3>$(_ 'Latest log entries')</h3>

<pre>
$(tail -n 5 $LOG | fgrep "-" | awk '{print $1, $2, $3, $4, $5, $6, $7}')
</pre>
EOT
		;;
esac

# xHTML 5 footer
export TEXTDOMAIN='tazpkg'
xhtml_footer
exit 0
