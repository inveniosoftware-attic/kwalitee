# -*- coding: utf-8 -*-
#
# This file is part of kwalitee
# Copyright (C) 2014 CERN.
#
# kwalitee is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# kwalitee is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with kwalitee; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Mocks and mixins for the tests."""

from __future__ import unicode_literals


GPL = """
{1} This file is part of kwalitee
{1} Copyright (C) {0} CERN.
{1}
{1} kwalitee is free software; you can redistribute it and/or
{1} modify it under the terms of the GNU General Public License as
{1} published by the Free Software Foundation; either version 2 of the
{1} License, or (at your option) any later version.
{1}
{1} kwalitee is distributed in the hope that it will be useful, but
{1} WITHOUT ANY WARRANTY; without even the implied warranty of
{1} MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
{1} General Public License for more details.
{1}
{1} You should have received a copy of the GNU General Public License
{1} along with kwalitee; if not, write to the Free Software Foundation,
{1} Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
{1}
{1} In applying this licence, CERN does not waive the privileges and immunities
{1} granted to it by virtue of its status as an Intergovernmental Organization
{1} or submit itself to any jurisdiction.
"""


class MyQueue(object):

    """Queue mock to use in place of the RQ queue.

    .. seealso:: `RQ <http://python-rq.org/docs/>`_
    """

    def __init__(self):
        """Initialize  an empty queue."""
        self.queue = []

    def __len__(self):
        """Length of the queue."""
        return len(self.queue)

    def dequeue(self):
        """Remove one item from the queue."""
        return self.queue.pop()

    def enqueue(self, *args, **kwargs):
        """Add items to the queue.

        :param args: tuple is appended to list
        :param kwargs: are ignored.
        """
        self.queue.insert(0, args)
