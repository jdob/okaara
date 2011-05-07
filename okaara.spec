%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

# -- header -----------------------------------------------------------------------

Name:		    okaara-lib
Version:        1.0.0
Release:	    1%{?dist}
Summary:	    Python command line utilities

Group:		    Development/Tools
License:	    GPLv2
URL:		    https://github.com/jdob/okaara
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)


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
