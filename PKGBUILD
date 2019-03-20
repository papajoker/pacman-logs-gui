# Maintainer: Papajoker <papajoke [at] manjaro [dot] fr>
_pkgname=pacman-logs-gui
pkgname=pacman-logs-gui-git
pkgver=r16.415eb1f.2019.03.20
pkgrel=1
pkgdesc="pacman logs gui gtk"
arch=('any')
license=('GPL')
replaces=("${pkgname%-*}")
conflicts=("${pkgname%-*}")
depends=('gtk3')
optdepends=('code' 'kate' 'gedit' 'leafpad')
makedepends=('git')
url="https://github.com/papajoker/${pkgname%-*}.git"
source=("app::git+${url}")

package() {
  cd "${srcdir}/app"
  mkdir -p "${pkgdir}/usr/lib/share/pacman-logs-gui"
  mkdir -p "${pkgdir}/usr/bin"
  mkdir -p "${pkgdir}/usr/share/applications"
  install -m 755 -D pacman-logs-gui "${pkgdir}/usr/bin/"
  install -m 644 -D pacman-logs.py pacman-logs.glade "${pkgdir}/usr/lib/share/pacman-logs-gui/"
  install -m 644 -D pacman-logs-gui.desktop "${pkgdir}/usr/share/applications/"
}

pkgver() {
  cd "$srcdir/app"
  printf "r%s.%s.%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)" "$(date +%Y%m%d)"
}

md5sums=('SKIP')
