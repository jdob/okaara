%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

# -- header -----------------------------------------------------------------------

Name:		    okaara-lib
Version:        1.0.2
Release:	    1%{?dist}
Summary:	    Python command line utilities

Group:		    Development/Tools
License:	    GPLv2
URL:		    https://github.com/jdob/okaara
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-setuptools
Requires:	    python >= 2.4


%description
Library of Python functions that facilitate the creation of command-line interfaces.


%prep
%setup -q


# -- build -----------------------------------------------------------------------

%build
pushd src
%{__python} setup.py build
popd


# -- install ---------------------------------------------------------------------

%install
rm -rf $RPM_BUILD_ROOT

# Python setup
pushd src
%{__python} setup.py install -O1 --skip-build --root %{buildroot}
popd
rm -f $RPM_BUILD_ROOT%{python_sitelib}/rhui*egg-info/requires.txt


# -- clean -----------------------------------------------------------------------

%clean
rm -rf $RPM_BUILD_ROOT



%files
%defattr(-,root,root,-)
%{python_sitelib}/okaara/*
%{python_sitelib}/okaara*.egg-info


# -- changelog -------------------------------------------------------------------

%changelog
* Mon Feb 06 2012 Jay Dobies <jason.dobies@redhat.com> 1.0.2-1
- Flushed out some unit tests (jason.dobies@redhat.com)
- Fixed typo (jason.dobies@redhat.com)
- Added interrupt simulation to the Script (jason.dobies@redhat.com)
- Ignoring PyCharm files and generated coverage reports
  (jason.dobies@redhat.com)
- Updated documentation for new approach to testing with prompts
  (jason.dobies@redhat.com)
- Added framework for shell documentation (jason.dobies@redhat.com)
- Tweaked testability classes (jason.dobies@redhat.com)
- Added prompt usage and examples (jason.dobies@redhat.com)
- These look better prefaced with get_ (jason.dobies@redhat.com)
- Added tag support for writes as well. Added utility methods to retrieve tags.
  (jason.dobies@redhat.com)
- Moved interruptable functionality to read method (jason.dobies@redhat.com)
- Added progress module usage documentation (jason.dobies@redhat.com)
- Use terminal size if not specified (jason.dobies@redhat.com)
- Overview page documentation (jason.dobies@redhat.com)
- Added shortcut to wrap from write() and terminal size calculation
  (jason.dobies@redhat.com)
- Updated copyright date and version (jason.dobies@redhat.com)
- Fixed documentation for ABORT (jason.dobies@redhat.com)
- More sphinx clean up (jason.dobies@redhat.com)
- Added wrapped iterator support to progress bar (jason.dobies@redhat.com)
- Migrated comments to rest syntax (jason.dobies@redhat.com)
- Updated docstrings for rest format (jason.dobies@redhat.com)
- Restructured docs index (jason.dobies@redhat.com)
- Removed generated docs from sphinx directory (jason.dobies@redhat.com)
- Initial implementation of sphinx documentation (jason.dobies@redhat.com)
- Fixed issue with usage rendering for sections (jason.dobies@redhat.com)
- Propagate flags to recursive call (jason.dobies@redhat.com)
- Module level docs (jason.dobies@redhat.com)
- Changed in place rendering technique to not use save/reset since it's not
  overly supported. (jason.dobies@redhat.com)
- Added spinner implementation (jason.dobies@redhat.com)
- Initial revision of the progress bar (jason.dobies@redhat.com)
- Added save/reset position calls (jason.dobies@redhat.com)
- Reworked clear behavior and added move command (jason.dobies@redhat.com)
- Added clear method and reordered file (jason.dobies@redhat.com)
- Added instance-level color disabling (jason.dobies@redhat.com)
- Changed default behavior to interruptable (jason.dobies@redhat.com)
- Added safe_start ability and enhanced rendering capabilities
  (jason.dobies@redhat.com)
- Added logic to calculate centering text (jason.dobies@redhat.com)
- Added auto-wrapping (jason.dobies@redhat.com)
- Added more colors (jason.dobies@redhat.com)
- Added first sample shell and made some fixes accordingly
  (jason.dobies@redhat.com)
- Continuing on prompt unit tests (jason.dobies@redhat.com)

* Sat May 07 2011 Jay Dobies <jason.dobies@redhat.com> 1.0.1-1
- First revision

