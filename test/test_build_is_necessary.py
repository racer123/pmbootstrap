"""
Copyright 2017 Oliver Smith

This file is part of pmbootstrap.

pmbootstrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pmbootstrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pmbootstrap.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import sys
import pytest

# Import from parent directory
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__) + "/..")))
import pmb.build.other


@pytest.fixture
def args(request, tmpdir):
    import pmb.parse
    sys.argv = ["pmbootstrap.py", "chroot"]
    args = pmb.parse.arguments()
    setattr(args, "logfd", open("/dev/null", "a+"))
    request.addfinalizer(args.logfd.close)
    request.addfinalizer(args.logfd.close)

    # Create an empty APKINDEX.tar.gz file, so we can use its path and
    # timestamp to put test information in the cache.
    apkindex_path = str(tmpdir) + "/APKINDEX.tar.gz"
    open(apkindex_path, "a").close()
    lastmod = os.path.getmtime(apkindex_path)
    args.cache["apkindex"][apkindex_path] = {"lastmod": lastmod, "ret": {}}
    return args


def test_build_is_necessary(args):
    # Prepare APKBUILD and APKINDEX data
    apkbuild = pmb.parse.apkbuild(args.aports + "/hello-world/APKBUILD")
    apkbuild["pkgver"] = "1"
    apkbuild["pkgrel"] = "2"
    apkindex_path = list(args.cache["apkindex"].keys())[0]
    args.cache["apkindex"][apkindex_path]["ret"] = {
        "hello-world": {"pkgname": "hello-world", "version": "1-r2"}
    }

    # a) Binary repo has a newer version
    args.cache["apkindex"][apkindex_path]["ret"][
        "hello-world"]["version"] = "999-r1"
    assert pmb.build.is_necessary(args, None, apkbuild, apkindex_path) is False

    # b) Aports folder has a newer version
    args.cache["apkindex"][apkindex_path][
        "ret"]["hello-world"]["version"] = "0-r0"
    assert pmb.build.is_necessary(args, None, apkbuild, apkindex_path) is True

    # c) Same version
    args.cache["apkindex"][apkindex_path][
        "ret"]["hello-world"]["version"] = "1-r2"

    # c.1) Newer timestamp in aport (timestamp in repo: 1970-01-01)
    args.cache["apkindex"][apkindex_path][
        "ret"]["hello-world"]["timestamp"] = "0"
    assert pmb.build.is_necessary(args, None, apkbuild, apkindex_path) is True

    # c.2) Newer timestamp in binary repo (timestamp in repo: 3000-01-01)
    args.cache["apkindex"][apkindex_path]["ret"][
        "hello-world"]["timestamp"] = "32503680000"
    assert pmb.build.is_necessary(args, None, apkbuild, apkindex_path) is False