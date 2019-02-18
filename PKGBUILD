# Maintainer: Papajoker <papajoke [at] manjaro [dot] fr>
pkgname=pacman-logs-gui
pkgver=0.4.0
pkgrel=1
pkgdesc="pacman logs gui gtk"
arch=('any')
license=('GPL')
depends=('gtk3')
optdepends=('code' 'kate' 'gedit' 'leafpad')
makedepends=('git')
source=("https://github.com/papajoker/${pkgname}/archive/${pkgver}.tar.gz")

package() {
  cd "${srcdir}/${pkgname}-${pkgver}"
  mkdir -p "${pkgdir}/usr/lib/share/pacman-logs-gui"
  mkdir -p "${pkgdir}/usr/bin"
  mkdir -p "${pkgdir}/usr/share/applications"
  cp pacman-logs-gui "${pkgdir}/usr/bin/"
  cp pacman-logs.py "${pkgdir}/usr/lib/share/pacman-logs-gui"
  cp pacman-logs.glade  "${pkgdir}/usr/lib/share/pacman-logs-gui"
  cp alpmtransform.py "${pkgdir}/usr/lib/share/pacman-logs-gui"
  cp pacman-logs-gui.desktop "${pkgdir}/usr/share/applications"
}

md5sums=('SKIP')
