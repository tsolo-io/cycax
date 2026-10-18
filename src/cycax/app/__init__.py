# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The CyCAx service layer: projects, targets, planning, building and the cache.

No printing and no input here. The CLI, the terminal UI and `cycax.build()` use this layer and
show its events (`cycax.app.events`).
"""
