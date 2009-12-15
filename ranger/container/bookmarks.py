import string
import re
import os
ALLOWED_KEYS = string.ascii_letters + string.digits + "`'"

class NonexistantBookmark(Exception):
	pass

class Bookmarks(object):
	"""Bookmarks is a container which associates keys with bookmarks.

A key is a string with: len(key) == 1 and key in ALLOWED_KEYS.

A bookmark is an object with: bookmark == bookmarktype(str(instance))
Which is true for str or FileSystemObject. This condition is required
so bookmark-objects can be saved to and loaded from a file.

Optionally, a bookmark.go() method is used for entering a bookmark.
"""

	last_mtime = None
	autosave = True
	load_pattern = re.compile(r"^[\d\w`']:.")

	def __init__(self, bookmarkfile, bookmarktype=str, autosave=False):
		"""<bookmarkfile> specifies the path to the file where
bookmarks are saved in.
"""
		self.autosave = autosave
		self.dct = {}
		self.path = bookmarkfile
		self.bookmarktype = bookmarktype

	def load(self):
		"""Load the bookmarks from path/bookmarks"""
		try:
			new_dict = self._load_dict()
		except OSError:
			return

		self._set_dict(new_dict)

	def delete(self, key):
		"""Delete the bookmark with the given key"""
		if key in self.dct:
			del self.dct[key]
			if self.autosave: self.save()

	def enter(self, key):
		"""Enter the bookmark with the given key.
Requires the bookmark instance to have a go() method.
"""

		try:
			return self[key].go()
		except (IndexError, KeyError, AttributeError):
			return False

	def update_if_outdated(self):
		if self.last_mtime != self._get_mtime():
			self.update()

	def remember(self, value):
		"""Bookmarks <value> to the keys ` and '"""
		self["`"] = value
		self["'"] = value
		if self.autosave: self.save()

	def __getitem__(self, key):
		"""Get the bookmark associated with the key"""
		if key in self.dct:
			return self.dct[key]
		else:
			raise NonexistantBookmark()

	def __setitem__(self, key, value):
		"""Bookmark <value> to the key <key>.
key is expected to be a 1-character string and element of ALLOWED_KEYS.
value is expected to be a filesystemobject."""
		if key in ALLOWED_KEYS:
			self.dct[key] = value
			if self.autosave: self.save()

	def __contains__(self, key):
		"""Test whether a bookmark-key is defined"""
		return key in self.dct

	def update(self):
		"""Update the bookmarks from the bookmark file.
Useful if two instances are running which define different bookmarks.
"""
		
		try:
			real_dict = self._load_dict()
		except OSError:
			return

		for key in set(self.dct.keys()) | set(real_dict.keys()):
			if key in self.dct:
				current = self.dct[key]
			else:
				current = None
			
			if key in self.original_dict:
				original = self.original_dict[key]
			else:
				original = None
				
			if key in real_dict:
				real = real_dict[key]
			else:
				real = None

			if current == original and current != real:
				continue

			if key not in self.dct:
				del real_dict[key]
			else:
				real_dict[key] = current

		self._set_dict(real_dict)

	def save(self):
		"""Save the bookmarks to the bookmarkfile.
This is done automatically after every modification if autosave is True."""
		import os
		self.update()
		if os.access(self.path, os.W_OK):
			f = open(self.path, 'w')
			for key, value in self.dct.items():
				if type(key) == str\
						and key in ALLOWED_KEYS:
					f.write("{0}:{1}\n".format(str(key), str(value)))

			f.close()
		self._update_mtime()

	def _load_dict(self):
		import os
		dct = {}
		if os.access(self.path, os.R_OK):
			f = open(self.path, 'r')
			for line in f:
				if self.load_pattern.match(line):
					key, value = line[0], line[2:-1]
					if key in ALLOWED_KEYS: 
						dct[key] = self.bookmarktype(value)
			f.close()
			return dct
		else:
			raise OSError('Cannot read the given path')
	
	def _set_dict(self, dct):
		self.dct.clear()
		self.dct.update(dct)
		self.original_dict = self.dct.copy()
		self._update_mtime()

	def _get_mtime(self):
		import os
		try:
			return os.stat(self.path).st_mtime
		except OSError:
			return None
	
	def _update_mtime(self):
		self.last_mtime = self._get_mtime()